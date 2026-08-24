# Crypto/OTC Transaction Idempotency & Duplicate-Payout Protection — Sprint 48.0.
# SECURITY-CRITICAL. Canonical service — do not re-implement this logic in
# Telegram handlers, Concierge/AI-command code, or frontend code. Every
# consumer (Telegram bot, Concierge, Web UI, Operator/manager UI, future API
# integrations) must call CryptoTxAntifraudEngine, directly (in-process,
# same Python runtime for bot/Concierge) or via the management API endpoint
# (platform_management-registered router, for Web/Operator UI and future
# integrations) that itself calls this same engine.
#
# Idempotency mechanism: CryptoIncomingTransaction's DB UniqueConstraint on
# (network, tx_hash, token, log_index) — see database/models/crypto_tx_registry.py.
# register_incoming() attempts the INSERT inside a SAVEPOINT
# (session.begin_nested()); a concurrent duplicate raises IntegrityError,
# which is caught, the savepoint is rolled back (not the whole transaction),
# and the pre-existing row is looked up and returned as a blocked duplicate.
# This is safe across concurrent *processes* (two operators, two bot
# instances, a web request and a bot request racing) because Postgres itself
# serializes conflicting inserts against a unique index — no in-process lock
# would give that guarantee.

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy.exc import IntegrityError

from database.models.audit_log import AuditAction
from database.models.crypto_tx_registry import CryptoIncomingTransaction, CryptoTxStatus
from database.session import get_session
from repositories.audit_repository import AuditRepository
from repositories.crypto_tx_registry_repository import CryptoTxRegistryRepository
from repositories.deal_engine_v1_repository import DealEngineV1Repository
from repositories.payment_engine_v1_repository import PaymentEngineV1Repository

logger = logging.getLogger(__name__)

# Requirement 10 — only these authenticated_role (bot) / ManagementRole (web)
# values may approve a duplicate override. Matches the "AUTHORIZATION
# (authenticated_role) != VIEW MODE (active_persona)" distinction already
# established in services/vertical_role_registry.py — override checks the
# real authenticated role, never the cosmetic active_persona/view-as role.
PRIVILEGED_OVERRIDE_ROLES = frozenset({"platform_owner", "owner", "manager", "supervisor"})

DUPLICATE_SUBMIT_WINDOW = timedelta(minutes=15)
OPERATOR_REPEAT_ATTEMPT_WINDOW = timedelta(minutes=10)
OPERATOR_REPEAT_ATTEMPT_THRESHOLD = 3


class CryptoAntifraudError(Exception):
    pass


class CryptoTxNotFoundError(CryptoAntifraudError):
    pass


class CryptoTxInvalidStateError(CryptoAntifraudError):
    pass


class CryptoTxOverrideDeniedError(CryptoAntifraudError):
    """Raised when override is attempted without a privileged role, without a
    reason, or without explicit confirmation. Requirement 6 / 10."""


class CryptoTxOverrideUnavailableError(CryptoAntifraudError):
    """Sprint 48.1 — raised on every approve_override() call, regardless of
    role/reason/confirmation. This codebase has no real step-up
    authentication (password re-entry, OTP, hardware key, etc.) — confirmed
    by inspecting platform_security/ during Sprint 48.1's audit; only a
    passing mention of "optional MFA / trusted device" exists, no actual
    verifier. A second button-tap or a client-supplied boolean is not
    authentication. Per Sprint 48.1's explicit requirement, faking reauth is
    worse than not having the feature: override is disabled by construction
    (see _verify_step_up_token, which always returns False) until a real
    step-up provider is wired in. Cancel and Send-for-review remain fully
    available — only the override action is affected."""


@dataclass(frozen=True)
class DuplicateWarning:
    """Everything requirement 4 says the warning must contain."""

    tx_hash: str
    network: str
    token: str
    amount: Decimal
    wallet_address: str
    previous_deal_id: str | None
    previous_payout_id: str | None
    previous_customer_id: int | None  # caller must redact per role before display
    previous_operator_id: int
    previous_status: str
    first_seen_at: datetime
    anomalies: list[str] = field(default_factory=list)
    # Sprint 48.1 — the real, legacy crypto_deals/crypto_payments reference
    # (see database/models/crypto_tx_registry.py for why this is separate
    # from previous_deal_id/previous_payout_id, which are UUID DealEngineV1/
    # PaymentEngineV1 references that crypto never populates today).
    previous_legacy_deal_id: int | None = None
    previous_legacy_payment_id: int | None = None


@dataclass(frozen=True)
class CryptoTxDecision:
    """Result of register_incoming(): either a clean registration or a
    blocked duplicate requiring one of the three requirement-5 actions."""

    is_duplicate: bool
    transaction: CryptoIncomingTransaction
    warning: DuplicateWarning | None = None


def _redact_customer_for_role(warning: DuplicateWarning, *, viewer_role: str) -> DuplicateWarning:
    """Requirement 4: "previous customer if allowed by role." Only privileged
    roles see the previous customer_id; everyone else gets it redacted."""
    if viewer_role in PRIVILEGED_OVERRIDE_ROLES:
        return warning
    return DuplicateWarning(**{**warning.__dict__, "previous_customer_id": None})


class CryptoTxAntifraudEngine:
    """Canonical Crypto/OTC anti-duplicate service. Stateless — every method
    opens its own DB session/transaction, safe to call concurrently from
    any consumer (bot, Concierge, management API)."""

    @staticmethod
    async def register_incoming(
        *,
        network: str,
        tx_hash: str,
        token: str,
        amount: Decimal,
        wallet_address: str,
        created_by: int,
        log_index: str = "0",
        deal_id: uuid.UUID | None = None,
        payout_id: uuid.UUID | None = None,
        legacy_deal_id: int | None = None,
        legacy_payment_id: int | None = None,
        customer_id: int | None = None,
        tenant_id: uuid.UUID | None = None,
        vertical: str = "crypto_otc",
        notes: str | None = None,
        viewer_role: str = "operator",
    ) -> CryptoTxDecision:
        """Requirement 1/2/3/4: persist a new incoming transfer, or — if this
        exact transaction identity is already registered — block and return
        a full duplicate warning instead of silently reusing it.

        deal_id/payout_id (UUID) and legacy_deal_id/legacy_payment_id (int)
        are two independent, mutually exclusive reference spaces — see
        database/models/crypto_tx_registry.py. Callers pass whichever one
        applies to their vertical; today only the legacy pair is ever
        populated (crypto/OTC has no DealEngineV1 presence)."""
        now = datetime.now(timezone.utc)
        is_reserved = bool(deal_id or payout_id or legacy_deal_id or legacy_payment_id)
        status = CryptoTxStatus.RESERVED.value if is_reserved else CryptoTxStatus.PENDING.value

        async with get_session() as session:
            repo = CryptoTxRegistryRepository(session)
            try:
                async with session.begin_nested():
                    row = await repo.create(
                        network=network,
                        tx_hash=tx_hash,
                        token=token,
                        log_index=log_index,
                        wallet_address=wallet_address,
                        amount=amount,
                        deal_id=deal_id,
                        payout_id=payout_id,
                        legacy_deal_id=legacy_deal_id,
                        legacy_payment_id=legacy_payment_id,
                        customer_id=customer_id,
                        status=status,
                        first_seen_at=now,
                        registered_by=created_by,
                        tenant_id=tenant_id,
                        vertical=vertical,
                        notes=notes,
                    )
            except IntegrityError:
                logger.info(
                    "crypto_tx_duplicate_insert_rejected network=%s tx_hash=%s token=%s",
                    network, tx_hash, token,
                )
                existing = await repo.get_by_identity(
                    network=network, tx_hash=tx_hash, token=token, log_index=log_index
                )
                if existing is None:  # pragma: no cover — pathological race, re-raise
                    raise
                anomalies = await CryptoTxAntifraudEngine._anomaly_checks(
                    session, existing, created_by=created_by
                )
                warning = DuplicateWarning(
                    tx_hash=existing.tx_hash,
                    network=existing.network,
                    token=existing.token,
                    amount=existing.amount,
                    wallet_address=existing.wallet_address,
                    previous_deal_id=str(existing.deal_id) if existing.deal_id else None,
                    previous_payout_id=str(existing.payout_id) if existing.payout_id else None,
                    previous_legacy_deal_id=existing.legacy_deal_id,
                    previous_legacy_payment_id=existing.legacy_payment_id,
                    previous_customer_id=existing.customer_id,
                    previous_operator_id=existing.registered_by,
                    previous_status=existing.status,
                    first_seen_at=existing.first_seen_at,
                    anomalies=anomalies,
                )
                warning = _redact_customer_for_role(warning, viewer_role=viewer_role)
                await AuditRepository(session).create_log(
                    entity_type="crypto_incoming_transaction",
                    entity_id=str(existing.id),
                    action=AuditAction.DUPLICATE_TX_DETECTED.value,
                    user_id=created_by,
                    new_value={"attempted_deal_id": str(deal_id) if deal_id else None,
                               "attempted_payout_id": str(payout_id) if payout_id else None,
                               "attempted_legacy_deal_id": legacy_deal_id,
                               "attempted_legacy_payment_id": legacy_payment_id},
                )
                # Requirement 4: BLOCK automatic processing by default.
                await AuditRepository(session).create_log(
                    entity_type="crypto_incoming_transaction",
                    entity_id=str(existing.id),
                    action=AuditAction.DUPLICATE_TX_BLOCKED.value,
                    user_id=created_by,
                )
                return CryptoTxDecision(is_duplicate=True, transaction=existing, warning=warning)

            await AuditRepository(session).create_log(
                entity_type="crypto_incoming_transaction",
                entity_id=str(row.id),
                action=AuditAction.CRYPTO_TX_REGISTERED.value,
                user_id=created_by,
                new_value={"status": row.status, "deal_id": str(deal_id) if deal_id else None},
            )
            return CryptoTxDecision(is_duplicate=False, transaction=row)

    @staticmethod
    async def check_duplicate(
        *, network: str, tx_hash: str, token: str, log_index: str = "0"
    ) -> CryptoIncomingTransaction | None:
        """Read-only lookup — requirement 3's "search the canonical registry"
        step, usable before committing to a full register_incoming() call."""
        async with get_session() as session:
            return await CryptoTxRegistryRepository(session).get_by_identity(
                network=network, tx_hash=tx_hash, token=token, log_index=log_index
            )

    @staticmethod
    async def complete_payout(
        transaction_id: uuid.UUID, *, actor_id: int, payout_id: uuid.UUID | None = None
    ) -> CryptoIncomingTransaction:
        async with get_session() as session:
            repo = CryptoTxRegistryRepository(session)
            row = await repo.get_by_id(transaction_id)
            if row is None:
                raise CryptoTxNotFoundError(str(transaction_id))
            if row.status not in (CryptoTxStatus.PENDING.value, CryptoTxStatus.RESERVED.value):
                raise CryptoTxInvalidStateError(
                    f"cannot complete payout from status {row.status}"
                )
            fields: dict[str, Any] = {"status": CryptoTxStatus.COMPLETED.value}
            if payout_id is not None:
                fields["payout_id"] = payout_id
            row = await repo.update(transaction_id, **fields)
            await AuditRepository(session).create_log(
                entity_type="crypto_incoming_transaction",
                entity_id=str(transaction_id),
                action=AuditAction.PAYOUT_COMPLETED.value,
                user_id=actor_id,
                new_value={"payout_id": str(payout_id) if payout_id else None},
            )
            return row

    @staticmethod
    async def cancel(transaction_id: uuid.UUID, *, actor_id: int, reason: str) -> CryptoIncomingTransaction:
        async with get_session() as session:
            repo = CryptoTxRegistryRepository(session)
            row = await repo.get_by_id(transaction_id)
            if row is None:
                raise CryptoTxNotFoundError(str(transaction_id))
            row = await repo.update(
                transaction_id, status=CryptoTxStatus.CANCELLED.value, notes=reason
            )
            await AuditRepository(session).create_log(
                entity_type="crypto_incoming_transaction",
                entity_id=str(transaction_id),
                action=AuditAction.UPDATE.value,
                user_id=actor_id,
                new_value={"status": CryptoTxStatus.CANCELLED.value, "reason": reason},
            )
            return row

    @staticmethod
    async def request_review(
        transaction_id: uuid.UUID, *, actor_id: int, reason: str | None = None
    ) -> CryptoIncomingTransaction:
        """Requirement 5: "Send for manual review / hold" — a regular
        operator/cashier action, does not require a privileged role."""
        async with get_session() as session:
            repo = CryptoTxRegistryRepository(session)
            row = await repo.get_by_id(transaction_id)
            if row is None:
                raise CryptoTxNotFoundError(str(transaction_id))
            await AuditRepository(session).create_log(
                entity_type="crypto_incoming_transaction",
                entity_id=str(transaction_id),
                action=AuditAction.DUPLICATE_TX_REVIEW_REQUESTED.value,
                user_id=actor_id,
                new_value={"reason": reason},
            )
            return row

    @staticmethod
    def _verify_step_up_token(step_up_token: str | None) -> bool:
        """Sprint 48.1 — the single seam a real step-up authentication
        provider (password re-entry, OTP, hardware key, etc.) plugs into.
        No such provider exists in this codebase today (confirmed during
        Sprint 48.1's audit: platform_security/ has no MFA/step-up
        verifier), so this always returns False by construction — it must
        NOT be replaced with a boolean the caller controls (that was Sprint
        48.0's `reauth_verified` flag, which this sprint removed precisely
        because a client-supplied flag is not authentication). Implementing
        a real provider means changing this function's body, not adding a
        parameter anywhere else."""
        return False

    @staticmethod
    async def approve_override(
        transaction_id: uuid.UUID,
        *,
        approver_id: int,
        approver_role: str,
        reason: str,
        confirmed: bool,
        new_deal_id: uuid.UUID | None = None,
        new_payout_id: uuid.UUID | None = None,
        new_legacy_deal_id: int | None = None,
        new_legacy_payment_id: int | None = None,
        step_up_token: str | None = None,
    ) -> CryptoIncomingTransaction:
        """Requirement 6: privileged role + explicit confirmation + mandatory
        reason + audit. Requirement 8: never overwrite the original
        deal_id/payout_id (or legacy_deal_id/legacy_payment_id) on the
        transaction row — the override is recorded as an additional
        CryptoTxOverrideLink row instead.

        Sprint 48.1: override is disabled in production. Real step-up
        re-authentication does not exist yet (see _verify_step_up_token), and
        per this sprint's explicit requirement, a fake substitute (a second
        button-tap, a client boolean) must not be accepted in its place.
        Role/confirmation/reason are still validated first — in that order —
        so callers get the most specific, correctly-audited rejection reason;
        but even a fully privileged, fully confirmed, fully-reasoned request
        is rejected at the final step until a real provider is wired into
        _verify_step_up_token."""
        if approver_role not in PRIVILEGED_OVERRIDE_ROLES:
            async with get_session() as session:
                await AuditRepository(session).create_log(
                    entity_type="crypto_incoming_transaction",
                    entity_id=str(transaction_id),
                    action=AuditAction.DUPLICATE_TX_OVERRIDE_REJECTED.value,
                    user_id=approver_id,
                    new_value={"reason": "insufficient_role", "role": approver_role},
                )
            raise CryptoTxOverrideDeniedError(
                f"role {approver_role!r} is not authorized to approve a duplicate override"
            )
        if not confirmed:
            raise CryptoTxOverrideDeniedError("explicit confirmation is required")
        if not reason or not reason.strip():
            raise CryptoTxOverrideDeniedError("a reason/comment is mandatory for an override")

        if not CryptoTxAntifraudEngine._verify_step_up_token(step_up_token):
            async with get_session() as session:
                await AuditRepository(session).create_log(
                    entity_type="crypto_incoming_transaction",
                    entity_id=str(transaction_id),
                    action=AuditAction.DUPLICATE_TX_OVERRIDE_REJECTED.value,
                    user_id=approver_id,
                    new_value={"reason": "override_unavailable_no_real_step_up_auth"},
                )
            raise CryptoTxOverrideUnavailableError(
                "duplicate override is disabled: no real step-up authentication is "
                "configured for this deployment yet; use Cancel or Send-for-review"
            )

        async with get_session() as session:  # pragma: no cover — unreachable until a real provider exists
            repo = CryptoTxRegistryRepository(session)
            row = await repo.get_by_id(transaction_id)
            if row is None:
                raise CryptoTxNotFoundError(str(transaction_id))

            await repo.create_override_link(
                transaction_id=transaction_id,
                deal_id=new_deal_id,
                payout_id=new_payout_id,
                legacy_deal_id=new_legacy_deal_id,
                legacy_payment_id=new_legacy_payment_id,
                approved_by=approver_id,
                reason=reason,
            )
            row = await repo.update(transaction_id, approved_by=approver_id)
            await AuditRepository(session).create_log(
                entity_type="crypto_incoming_transaction",
                entity_id=str(transaction_id),
                action=AuditAction.DUPLICATE_TX_OVERRIDE_APPROVED.value,
                user_id=approver_id,
                new_value={
                    "reason": reason,
                    "new_deal_id": str(new_deal_id) if new_deal_id else None,
                    "new_payout_id": str(new_payout_id) if new_payout_id else None,
                    "new_legacy_deal_id": new_legacy_deal_id,
                    "new_legacy_payment_id": new_legacy_payment_id,
                    # original linkage is intentionally NOT touched/duplicated
                    # here — it remains readable directly on `row`.
                },
            )
            return row

    @staticmethod
    async def reject_override(
        transaction_id: uuid.UUID, *, actor_id: int, reason: str | None = None
    ) -> None:
        async with get_session() as session:
            await AuditRepository(session).create_log(
                entity_type="crypto_incoming_transaction",
                entity_id=str(transaction_id),
                action=AuditAction.DUPLICATE_TX_OVERRIDE_REJECTED.value,
                user_id=actor_id,
                new_value={"reason": reason},
            )

    # --- Requirement 9: anomaly checks beyond exact tx_hash equality ---

    @staticmethod
    async def _anomaly_checks(
        session, existing: CryptoIncomingTransaction, *, created_by: int
    ) -> list[str]:
        anomalies: list[str] = []
        repo = CryptoTxRegistryRepository(session)

        # same tx_hash submitted after prior cancellation/closure
        terminal = await repo.list_terminal_conflicts(
            network=existing.network, tx_hash=existing.tx_hash, token=existing.token
        )
        if any(t.status == CryptoTxStatus.CANCELLED.value for t in terminal):
            anomalies.append("resubmitted_after_cancellation")

        # same wallet + amount in a suspiciously short window
        near_dupes = await repo.recent_by_wallet_and_amount(
            wallet_address=existing.wallet_address,
            amount=existing.amount,
            window=DUPLICATE_SUBMIT_WINDOW,
            exclude_id=existing.id,
        )
        if near_dupes:
            anomalies.append("same_wallet_amount_short_window")

        # same transfer linked to multiple customers (original + any
        # override links' deals, each looked up for their client_id)
        customers: set[int] = set()
        if existing.customer_id is not None:
            customers.add(existing.customer_id)
        links = await repo.list_override_links(existing.id)
        if links:
            deal_repo = DealEngineV1Repository(session)
            payment_repo = PaymentEngineV1Repository(session)
            for link in links:
                if link.deal_id is not None:
                    deal = await deal_repo.get_by_id(link.deal_id)
                    if deal is not None and getattr(deal, "client_id", None) is not None:
                        customers.add(deal.client_id)
                if link.payout_id is not None:
                    payment = await payment_repo.get_by_id(link.payout_id)
                    if payment is not None and getattr(payment, "client_id", None) is not None:
                        customers.add(payment.client_id)
        if len(customers) > 1:
            anomalies.append("linked_to_multiple_customers")

        # conflicting network/token metadata for what claims to be the same
        # underlying transfer (best-effort: same tx_hash, different
        # network/token combination already registered elsewhere)
        # handled naturally by the identity tuple itself — a genuinely
        # different (network, token) pair with the same tx_hash is a
        # *different* row by design, so surface it explicitly here.
        # (No separate query needed: this function is only called once a
        # duplicate on the *same* identity is already found, so a
        # same-hash-different-network row would need its own check —
        # left as a repository extension point, not silently claimed done.)

        # repeated payout attempts by the same operator/session
        attempts = await repo.count_payout_attempts_by_operator(
            created_by=created_by, window=OPERATOR_REPEAT_ATTEMPT_WINDOW
        )
        if attempts >= OPERATOR_REPEAT_ATTEMPT_THRESHOLD:
            anomalies.append("repeated_operator_attempts")

        return anomalies


crypto_tx_antifraud_engine = CryptoTxAntifraudEngine()
