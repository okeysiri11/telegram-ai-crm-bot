# Crypto/OTC canonical payout orchestration — Sprint 48.1.
# SECURITY-CRITICAL. This is the ONLY module Telegram and Web are allowed to
# call to confirm a crypto/OTC payout. Neither surface may call
# services.pg_crypto_tx_antifraud_engine.CryptoTxAntifraudEngine directly for
# a payout confirmation, and neither may call database.update_crypto_payment_status
# / update_crypto_deal_status directly — doing either would let one surface
# silently diverge from the other's anti-fraud behavior, which is exactly
# what this sprint's requirement forbids ("Telegram and Web must NOT
# implement independent payout rules").
#
# Canonical flow (see docs/SPRINT_48_1_RESULT.md for the full rationale):
#   validate deal/payment + current state
#   -> CryptoTxAntifraudEngine.register_incoming() [atomic claim of tx_hash,
#      DB UniqueConstraint is the final concurrency guarantee]
#   -> if duplicate: STOP here, return the warning — no state transition
#   -> execute the existing canonical legacy payment/deal transition
#      (database.update_crypto_payment_status, the real production
#      mechanism — see this sprint's RESULT doc for why DealEngineV1/
#      PaymentEngineV1 are NOT used: crypto is not a supported vertical
#      there, "auto"/"agro" only)
#   -> CryptoTxAntifraudEngine.complete_payout() [finalizes the antifraud
#      registry row + its own audit entry]
#
# Why legacy_deal_id/legacy_payment_id and not deal_id/payout_id: see
# database/models/crypto_tx_registry.py and this sprint's migration
# docstring. This module is the migration-friendly boundary — when crypto
# is eventually migrated into DealEngineV1 (tracked separately, NOT part of
# this sprint), only the body of confirm_payout() changes; Telegram/Web's
# calls into this module do not.

from __future__ import annotations

import enum
import logging
import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from database.models.crypto_tx_registry import CryptoIncomingTransaction, CryptoTxStatus
from services.pg_crypto_tx_antifraud_engine import (
    CryptoAntifraudError,
    CryptoTxAntifraudEngine,
    CryptoTxOverrideDeniedError,
    CryptoTxOverrideUnavailableError,
    DuplicateWarning,
)

logger = logging.getLogger(__name__)

__all__ = [
    "CryptoPayoutOrchestrator",
    "CryptoPayoutOrchestratorError",
    "CryptoDealNotFoundError",
    "CryptoDealInvalidStateError",
    "CryptoPayoutResultStatus",
    "CryptoPayoutResult",
    "CryptoAntifraudError",
    "CryptoTxOverrideDeniedError",
    "CryptoTxOverrideUnavailableError",
]


class CryptoPayoutOrchestratorError(Exception):
    pass


class CryptoDealNotFoundError(CryptoPayoutOrchestratorError):
    pass


class CryptoDealInvalidStateError(CryptoPayoutOrchestratorError):
    pass


class CryptoPayoutResultStatus(str, enum.Enum):
    CONFIRMED = "confirmed"
    DUPLICATE = "duplicate"
    ALREADY_CONFIRMED = "already_confirmed"  # idempotent retry, not a new payout


@dataclass(frozen=True)
class CryptoPayoutResult:
    status: CryptoPayoutResultStatus
    transaction: CryptoIncomingTransaction | None
    deal_id: int
    payment_id: int | None
    warning: DuplicateWarning | None = None


# Deal statuses that must never accept a new payout confirmation attempt.
_TERMINAL_DEAL_STATUSES = frozenset({"COMPLETED", "CANCELLED"})
# crypto_deals column order, per database_legacy.py::get_crypto_deal's SELECT *
# (also documented at format_crypto_deal_text's unpack) — indexed access is
# the existing convention in this legacy module; duplicated here rather than
# imported because database_legacy has no typed row model to import.
_DEAL_STATUS_IDX = 10
_DEAL_PAYMENT_STATUS_IDX = 11
_DEAL_CLIENT_ID_IDX = 1
_DEAL_AMOUNT_IDX = 5
_DEAL_CURRENCY_IDX = 6


def _unpack_deal(deal: tuple) -> dict[str, Any]:
    return {
        "id": deal[0],
        "client_id": deal[_DEAL_CLIENT_ID_IDX],
        "amount": deal[_DEAL_AMOUNT_IDX],
        "currency": deal[_DEAL_CURRENCY_IDX],
        "status": deal[_DEAL_STATUS_IDX],
        "payment_status": deal[_DEAL_PAYMENT_STATUS_IDX],
    }


class CryptoPayoutOrchestrator:
    """The canonical payout service for Sprint 48.1. Stateless; every method
    resolves its own legacy row and delegates duplicate-detection state to
    CryptoTxAntifraudEngine. Telegram (routers/crypto_tx_antifraud_router.py)
    and Web (platform_management/crypto_tx_antifraud_routes.py) both call
    this and only this for a payout action."""

    @staticmethod
    async def get_deal_summary(deal_id: int) -> dict[str, Any]:
        """Real, current state of a real crypto/OTC deal — used by both the
        Telegram deal-detail screen and the Web payout panel so neither
        renders a demo/stale view."""
        from database import get_crypto_deal, get_crypto_payment_for_deal

        deal = get_crypto_deal(deal_id)
        if not deal:
            raise CryptoDealNotFoundError(str(deal_id))
        summary = _unpack_deal(deal)
        payment = get_crypto_payment_for_deal(deal_id)
        summary["payment_id"] = payment[0] if payment else None
        summary["can_confirm_payout"] = (
            summary["status"] not in _TERMINAL_DEAL_STATUSES
            and summary["payment_status"] != "PAYMENT_RECEIVED"
            and summary["payment_status"] != "PAYMENT_CONFIRMED"
            and summary["payment_status"] != "DELIVERED"
        )
        return summary

    @staticmethod
    async def confirm_payout(
        *,
        deal_id: int,
        network: str,
        tx_hash: str,
        token: str,
        amount: Decimal,
        wallet_address: str,
        actor_id: int,
        actor_role: str,
        log_index: str = "0",
    ) -> CryptoPayoutResult:
        """The only path that may move a real crypto/OTC deal's payment
        status to PAYMENT_RECEIVED. No caller (bot, web, future integration)
        may reach that transition any other way."""
        from database import (
            create_crypto_payment,
            get_crypto_deal,
            get_crypto_payment_for_deal,
            update_crypto_payment_status,
        )

        if not tx_hash or not tx_hash.strip():
            raise CryptoDealInvalidStateError("tx_hash is required")
        tx_hash = tx_hash.strip()
        network = network.strip().upper()
        token = token.strip().upper()

        deal = get_crypto_deal(deal_id)
        if not deal:
            raise CryptoDealNotFoundError(str(deal_id))
        info = _unpack_deal(deal)
        if info["status"] in _TERMINAL_DEAL_STATUSES:
            raise CryptoDealInvalidStateError(
                f"deal {deal_id} is {info['status']}; cannot confirm a new payout"
            )

        payment_row = get_crypto_payment_for_deal(deal_id)
        payment_id = payment_row[0] if payment_row else None
        current_payment_status = payment_row[4] if payment_row else None
        if payment_id is None:
            payment_id = create_crypto_payment(
                deal_id, actor_id, float(amount), info["currency"] or "USD"
            )

        # Idempotent retry (Sprint 48.1 requirement): the *same* operator
        # action retried (double-tap, timeout+resend) against a payment that
        # is already confirmed against this exact tx_hash must succeed
        # quietly, not surface a "possible fraud" warning. Distinguish this
        # from a genuine duplicate (a *different* deal/payment reusing the
        # same tx_hash) by checking the existing row's legacy reference.
        existing = await CryptoTxAntifraudEngine.check_duplicate(
            network=network, tx_hash=tx_hash, token=token, log_index=log_index
        )
        if (
            existing is not None
            and existing.legacy_deal_id == deal_id
            and existing.legacy_payment_id == payment_id
            and existing.status == CryptoTxStatus.COMPLETED.value
        ):
            logger.info(
                "crypto_payout_idempotent_retry deal_id=%s payment_id=%s tx_hash=%s",
                deal_id, payment_id, tx_hash,
            )
            return CryptoPayoutResult(
                status=CryptoPayoutResultStatus.ALREADY_CONFIRMED,
                transaction=existing,
                deal_id=deal_id,
                payment_id=payment_id,
            )

        # Anti-fraud gate — atomic claim/register. No payout state
        # transition may occur before this returns is_duplicate=False.
        decision = await CryptoTxAntifraudEngine.register_incoming(
            network=network,
            tx_hash=tx_hash,
            token=token,
            amount=amount,
            wallet_address=wallet_address,
            created_by=actor_id,
            log_index=log_index,
            legacy_deal_id=deal_id,
            legacy_payment_id=payment_id,
            customer_id=info["client_id"],
            viewer_role=actor_role,
        )
        if decision.is_duplicate:
            # STOP — the existing canonical legacy transition is never called.
            return CryptoPayoutResult(
                status=CryptoPayoutResultStatus.DUPLICATE,
                transaction=decision.transaction,
                warning=decision.warning,
                deal_id=deal_id,
                payment_id=payment_id,
            )

        # Anti-fraud gate passed — now, and only now, execute the existing
        # canonical legacy payment/deal state transition.
        update_crypto_payment_status(payment_id, "PAYMENT_RECEIVED", actor_id)
        completed = await CryptoTxAntifraudEngine.complete_payout(
            decision.transaction.id, actor_id=actor_id
        )
        return CryptoPayoutResult(
            status=CryptoPayoutResultStatus.CONFIRMED,
            transaction=completed,
            deal_id=deal_id,
            payment_id=payment_id,
        )

    @staticmethod
    async def cancel(
        transaction_id: uuid.UUID, *, actor_id: int, reason: str
    ) -> CryptoIncomingTransaction:
        return await CryptoTxAntifraudEngine.cancel(transaction_id, actor_id=actor_id, reason=reason)

    @staticmethod
    async def request_review(
        transaction_id: uuid.UUID, *, actor_id: int, reason: str | None = None
    ) -> CryptoIncomingTransaction:
        return await CryptoTxAntifraudEngine.request_review(
            transaction_id, actor_id=actor_id, reason=reason
        )

    @staticmethod
    async def approve_override(
        transaction_id: uuid.UUID,
        *,
        approver_id: int,
        approver_role: str,
        reason: str,
        confirmed: bool,
        step_up_token: str | None = None,
    ) -> CryptoIncomingTransaction:
        """Always raises CryptoTxOverrideUnavailableError (after role/reason/
        confirmation validation) until a real step-up provider exists — see
        services.pg_crypto_tx_antifraud_engine.CryptoTxAntifraudEngine
        ._verify_step_up_token. Not implemented differently here; this is a
        thin pass-through so Telegram/Web have exactly one call site."""
        return await CryptoTxAntifraudEngine.approve_override(
            transaction_id,
            approver_id=approver_id,
            approver_role=approver_role,
            reason=reason,
            confirmed=confirmed,
            step_up_token=step_up_token,
        )

    @staticmethod
    async def reject_override(
        transaction_id: uuid.UUID, *, actor_id: int, reason: str | None = None
    ) -> None:
        await CryptoTxAntifraudEngine.reject_override(transaction_id, actor_id=actor_id, reason=reason)


crypto_payout_orchestrator = CryptoPayoutOrchestrator()
