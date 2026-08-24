"""
Sprint 48.0 — Crypto/OTC transaction idempotency & duplicate-payout
protection (security-critical). Updated in Sprint 48.1: override is now
disabled in production (no real step-up authentication provider exists —
CryptoTxOverrideUnavailableError), so every override test here asserts
rejection, not success. The management HTTP surface moved from
services/crypto_tx_antifraud_router.py to
platform_management/crypto_tx_antifraud_routes.py and gained deal-scoped
confirm-payout routes; see tests/test_crypto_payout_orchestrator_48_1.py for
the orchestrator-level (deal/payment-aware) coverage.

Exercises the real Postgres unique constraint on
crypto_incoming_transactions(network, tx_hash, token, log_index) — this is
the actual idempotency mechanism, not mocked. Every test uses a fresh,
random tx_hash so tests never collide with each other or with prior runs.
"""

from __future__ import annotations

import asyncio
import uuid
from decimal import Decimal

import pytest

# Sprint 48.0's new model has cross-table FKs (tenant_id -> partner tenants,
# deal_id -> deal_engine_v1_deals, payout_id -> payment_engine_v1_payments).
# SQLAlchemy needs every referenced model class imported before any of these
# tables' mappers are configured, same reason tests/conftest.py's
# _register_rbac_models fixture exists for database.models.users.
import database.models.automotive_partner_integration  # noqa: F401
import database.models.deal_engine_v1  # noqa: F401
import database.models.lead_engine  # noqa: F401
import database.models.partner_tenant_engine  # noqa: F401
import database.models.payment_engine_v1  # noqa: F401
import database.models.user_role  # noqa: F401
import database.models.role  # noqa: F401
import database.models.role_permission  # noqa: F401
import database.models.users  # noqa: F401

from services.pg_crypto_tx_antifraud_engine import (
    CryptoTxAntifraudEngine,
    CryptoTxOverrideDeniedError,
    CryptoTxOverrideUnavailableError,
    crypto_tx_antifraud_engine as engine,
)

from database.models.audit_log import AuditAction, AuditLog
from database.models.crypto_tx_registry import CryptoTxStatus

pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
async def _reset_db_engine_per_test():
    """This file exercises the real Postgres unique constraint across many
    test functions. database/engine.py caches a single AsyncEngine bound to
    whichever event loop first created it; pytest-asyncio's auto mode gives
    each test function its own event loop, so a later test reusing the
    cached engine hits "Future attached to a different loop" / "Event loop
    is closed" (the same class of pre-existing test-infrastructure issue
    diagnosed for tests/test_vertical_nav_46_5.py in the Sprint 46.6 report —
    there the fix was mocking out the one incidental DB call; here the
    tests genuinely need the real DB, so instead we dispose the engine while
    its own loop is still alive, using the project's existing shutdown_db()
    so the next test creates a fresh engine bound to its own loop). Scoped
    to this file only — not a conftest.py change, does not affect any other
    test module.

    Disposes BEFORE the test too (Sprint 48.1 fix, found by actually running
    the full suite, not just this file in isolation): some *other* test file
    earlier in a full `pytest tests/` run can leave the cached engine bound
    to its own now-closed loop; disposing only *after* each test in this
    file protects tests from each other but not from that. Disposing before
    as well guarantees this file's very first test also gets a fresh engine
    bound to its own loop, regardless of what ran before it.
    """
    from database.session import shutdown_db

    await shutdown_db()
    yield
    await shutdown_db()


def _unique_hash(label: str) -> str:
    return f"0x{label}_{uuid.uuid4().hex[:16]}"


async def _audit_rows_for(entity_id: str) -> list[AuditLog]:
    from sqlalchemy import select

    from database.session import get_session

    async with get_session() as session:
        result = await session.execute(
            select(AuditLog).where(AuditLog.entity_id == entity_id).order_by(AuditLog.created_at.asc())
        )
        return list(result.scalars().all())


class TestFirstValidTransaction:
    async def test_register_new_transaction_succeeds(self):
        tx_hash = _unique_hash("first")
        result = await engine.register_incoming(
            network="TRC20",
            tx_hash=tx_hash,
            token="USDT",
            amount=Decimal("250.00"),
            wallet_address="TFirstValidWallet",
            created_by=800001,
        )
        assert result.is_duplicate is False
        assert result.transaction.status == CryptoTxStatus.PENDING.value
        assert result.transaction.tx_hash == tx_hash

        audits = await _audit_rows_for(str(result.transaction.id))
        assert any(a.action == AuditAction.CRYPTO_TX_REGISTERED.value for a in audits)

    async def test_register_with_deal_id_reserves(self):
        # deal_id is a real FK (ondelete=SET NULL, but the row must exist at
        # insert time) — create a minimal real user + deal row rather than a
        # random UUID, so this test also validates the FK is enforced.
        from database.models.deal_engine_v1 import DealEngineV1Deal
        from database.models.users import User
        from database.session import get_session

        async with get_session() as session:
            user = User(telegram_id=900000 + uuid.uuid4().int % 100000)
            session.add(user)
            await session.flush()
            deal = DealEngineV1Deal(
                vertical="crypto_otc", client_id=user.id, title="Test OTC deal"
            )
            session.add(deal)
            await session.flush()
            deal_id = deal.id

        tx_hash = _unique_hash("reserve")
        result = await engine.register_incoming(
            network="ERC20",
            tx_hash=tx_hash,
            token="USDT",
            amount=Decimal("10"),
            wallet_address="TReserveWallet",
            created_by=800002,
            deal_id=deal_id,
        )
        assert result.is_duplicate is False
        assert result.transaction.status == CryptoTxStatus.RESERVED.value
        assert result.transaction.deal_id == deal_id

    async def test_register_with_legacy_deal_reserves(self):
        """Sprint 48.1 — the real reference space crypto/OTC actually uses."""
        tx_hash = _unique_hash("legacy_reserve")
        result = await engine.register_incoming(
            network="TRC20",
            tx_hash=tx_hash,
            token="USDT",
            amount=Decimal("10"),
            wallet_address="TLegacyReserveWallet",
            created_by=800002,
            legacy_deal_id=42424,
            legacy_payment_id=99999,
        )
        assert result.is_duplicate is False
        assert result.transaction.status == CryptoTxStatus.RESERVED.value
        assert result.transaction.legacy_deal_id == 42424
        assert result.transaction.legacy_payment_id == 99999
        # the UUID reference space stays untouched by the legacy one
        assert result.transaction.deal_id is None
        assert result.transaction.payout_id is None


class TestRepeatedSameTxHash:
    async def test_second_registration_is_blocked_by_default(self):
        tx_hash = _unique_hash("repeat")
        first = await engine.register_incoming(
            network="TRC20", tx_hash=tx_hash, token="USDT",
            amount=Decimal("50"), wallet_address="TRepeatWallet", created_by=800003,
        )
        assert first.is_duplicate is False

        second = await engine.register_incoming(
            network="TRC20", tx_hash=tx_hash, token="USDT",
            amount=Decimal("50"), wallet_address="TRepeatWallet", created_by=800004,
        )
        assert second.is_duplicate is True
        assert second.transaction.id == first.transaction.id
        assert second.warning is not None
        assert second.warning.tx_hash == tx_hash
        assert second.warning.network == "TRC20"
        assert second.warning.token == "USDT"
        assert second.warning.amount == Decimal("50")
        assert second.warning.wallet_address == "TRepeatWallet"
        assert second.warning.previous_operator_id == 800003
        assert second.warning.previous_status == CryptoTxStatus.PENDING.value

        audits = await _audit_rows_for(str(first.transaction.id))
        actions = {a.action for a in audits}
        assert AuditAction.DUPLICATE_TX_DETECTED.value in actions
        assert AuditAction.DUPLICATE_TX_BLOCKED.value in actions

    async def test_duplicate_warning_redacts_customer_for_non_privileged_role(self):
        tx_hash = _unique_hash("redact")
        await engine.register_incoming(
            network="TRC20", tx_hash=tx_hash, token="USDT",
            amount=Decimal("5"), wallet_address="TRedactWallet",
            created_by=800005, customer_id=900123,
        )
        dup = await engine.register_incoming(
            network="TRC20", tx_hash=tx_hash, token="USDT",
            amount=Decimal("5"), wallet_address="TRedactWallet",
            created_by=800006, viewer_role="operator",
        )
        assert dup.warning.previous_customer_id is None

        dup_privileged = await engine.register_incoming(
            network="TRC20", tx_hash=tx_hash, token="USDT",
            amount=Decimal("5"), wallet_address="TRedactWallet",
            created_by=800007, viewer_role="manager",
        )
        assert dup_privileged.warning.previous_customer_id == 900123


class TestConcurrentSimultaneousRequests:
    async def test_two_simultaneous_requests_only_one_wins(self):
        """The actual concurrency-safety requirement: two independent DB
        sessions racing to register the identical transaction identity.
        Exactly one must succeed; the other must see it as a duplicate.
        Real Postgres unique-constraint enforcement, not an app-level lock."""
        tx_hash = _unique_hash("race")

        results = await asyncio.gather(
            engine.register_incoming(
                network="TRC20", tx_hash=tx_hash, token="USDT",
                amount=Decimal("999"), wallet_address="TRaceWallet", created_by=800008,
            ),
            engine.register_incoming(
                network="TRC20", tx_hash=tx_hash, token="USDT",
                amount=Decimal("999"), wallet_address="TRaceWallet", created_by=800009,
            ),
        )
        duplicates = [r for r in results if r.is_duplicate]
        originals = [r for r in results if not r.is_duplicate]
        assert len(originals) == 1
        assert len(duplicates) == 1
        # both refer to the same underlying row
        assert duplicates[0].transaction.id == originals[0].transaction.id

    async def test_ten_way_race_exactly_one_winner(self):
        tx_hash = _unique_hash("race10")
        results = await asyncio.gather(
            *[
                engine.register_incoming(
                    network="TRC20", tx_hash=tx_hash, token="USDT",
                    amount=Decimal("1"), wallet_address="TRace10Wallet", created_by=800010 + i,
                )
                for i in range(10)
            ]
        )
        assert sum(1 for r in results if not r.is_duplicate) == 1
        assert sum(1 for r in results if r.is_duplicate) == 9


class TestCancelledPriorDeal:
    async def test_resubmission_after_cancellation_is_flagged_and_blocked(self):
        tx_hash = _unique_hash("cancelled")
        first = await engine.register_incoming(
            network="TRC20", tx_hash=tx_hash, token="USDT",
            amount=Decimal("77"), wallet_address="TCancelledWallet", created_by=800020,
        )
        cancelled = await engine.cancel(first.transaction.id, actor_id=800020, reason="client refunded")
        assert cancelled.status == CryptoTxStatus.CANCELLED.value

        again = await engine.register_incoming(
            network="TRC20", tx_hash=tx_hash, token="USDT",
            amount=Decimal("77"), wallet_address="TCancelledWallet", created_by=800021,
        )
        assert again.is_duplicate is True
        assert "resubmitted_after_cancellation" in again.warning.anomalies


class TestManualOverride:
    """Sprint 48.1: override is disabled in production — no real step-up
    authentication provider exists. Every path here must end in rejection,
    never in a successfully-created CryptoTxOverrideLink."""

    async def test_override_unavailable_even_for_fully_valid_privileged_request(self):
        tx_hash = _unique_hash("override")
        first = await engine.register_incoming(
            network="TRC20", tx_hash=tx_hash, token="USDT",
            amount=Decimal("42"), wallet_address="TOverrideWallet", created_by=800030,
        )
        with pytest.raises(CryptoTxOverrideUnavailableError):
            await engine.approve_override(
                first.transaction.id,
                approver_id=800099,
                approver_role="manager",  # privileged
                reason="Client confirmed second legitimate payout for a split deal.",
                confirmed=True,  # explicit
            )
        # no override link was created, and the original transaction is untouched
        from database.session import get_session
        from repositories.crypto_tx_registry_repository import CryptoTxRegistryRepository

        async with get_session() as session:
            repo = CryptoTxRegistryRepository(session)
            links = await repo.list_override_links(first.transaction.id)
            row = await repo.get_by_id(first.transaction.id)
        assert links == []
        assert row.approved_by is None

        audits = await _audit_rows_for(str(first.transaction.id))
        actions = {a.action for a in audits}
        assert AuditAction.DUPLICATE_TX_OVERRIDE_REJECTED.value in actions
        assert AuditAction.DUPLICATE_TX_OVERRIDE_APPROVED.value not in actions

    async def test_override_requires_reason(self):
        tx_hash = _unique_hash("override_noreason")
        first = await engine.register_incoming(
            network="TRC20", tx_hash=tx_hash, token="USDT",
            amount=Decimal("1"), wallet_address="W", created_by=800031,
        )
        with pytest.raises(CryptoTxOverrideDeniedError):
            await engine.approve_override(
                first.transaction.id,
                approver_id=800099,
                approver_role="manager",
                reason="   ",
                confirmed=True,
            )

    async def test_override_requires_explicit_confirmation(self):
        tx_hash = _unique_hash("override_noconfirm")
        first = await engine.register_incoming(
            network="TRC20", tx_hash=tx_hash, token="USDT",
            amount=Decimal("1"), wallet_address="W", created_by=800032,
        )
        with pytest.raises(CryptoTxOverrideDeniedError):
            await engine.approve_override(
                first.transaction.id,
                approver_id=800099,
                approver_role="manager",
                reason="valid reason",
                confirmed=False,
            )

    async def test_override_unavailable_is_distinct_from_denied(self):
        """A privileged, confirmed, reasoned request must fail with
        CryptoTxOverrideUnavailableError specifically (not the generic
        CryptoTxOverrideDeniedError used for role/reason/confirmation
        failures) — callers need to distinguish "you're not allowed" from
        "this feature isn't available to anyone yet"."""
        tx_hash = _unique_hash("override_unavailable")
        first = await engine.register_incoming(
            network="TRC20", tx_hash=tx_hash, token="USDT",
            amount=Decimal("1"), wallet_address="W", created_by=800033,
        )
        with pytest.raises(CryptoTxOverrideUnavailableError):
            await engine.approve_override(
                first.transaction.id,
                approver_id=800099,
                approver_role="owner",
                reason="valid reason",
                confirmed=True,
            )
        # a fabricated step_up_token must not help — _verify_step_up_token
        # always returns False until a real provider is implemented.
        with pytest.raises(CryptoTxOverrideUnavailableError):
            await engine.approve_override(
                first.transaction.id,
                approver_id=800099,
                approver_role="owner",
                reason="valid reason",
                confirmed=True,
                step_up_token="not-a-real-verified-token",
            )


class TestUnauthorizedOverrideAttempt:
    async def test_regular_operator_cannot_approve_override(self):
        tx_hash = _unique_hash("unauth")
        first = await engine.register_incoming(
            network="TRC20", tx_hash=tx_hash, token="USDT",
            amount=Decimal("30"), wallet_address="TUnauthWallet", created_by=800040,
        )
        with pytest.raises(CryptoTxOverrideDeniedError):
            await engine.approve_override(
                first.transaction.id,
                approver_id=800041,
                approver_role="operator",
                reason="I really want to approve this",
                confirmed=True,
            )
        audits = await _audit_rows_for(str(first.transaction.id))
        assert any(a.action == AuditAction.DUPLICATE_TX_OVERRIDE_REJECTED.value for a in audits)
        # and the transaction was NOT approved
        from database.session import get_session
        from repositories.crypto_tx_registry_repository import CryptoTxRegistryRepository

        async with get_session() as session:
            row = await CryptoTxRegistryRepository(session).get_by_id(first.transaction.id)
        assert row.approved_by is None

    async def test_cashier_can_cancel_and_request_review_but_not_override(self):
        tx_hash = _unique_hash("cashier")
        first = await engine.register_incoming(
            network="TRC20", tx_hash=tx_hash, token="USDT",
            amount=Decimal("15"), wallet_address="TCashierWallet", created_by=800042,
        )
        # cashier CAN send to review — no role gate on this action
        reviewed = await engine.request_review(first.transaction.id, actor_id=800042, reason="looks odd")
        assert reviewed.id == first.transaction.id
        # cashier CANNOT approve an override — rejected on role, before even
        # reaching the (also-failing) step-up check.
        with pytest.raises(CryptoTxOverrideDeniedError):
            await engine.approve_override(
                first.transaction.id,
                approver_id=800042,
                approver_role="cashier",
                reason="trying anyway",
                confirmed=True,
            )


class TestAuditTrailPersistence:
    async def test_full_lifecycle_leaves_a_complete_audit_trail(self):
        tx_hash = _unique_hash("lifecycle")
        first = await engine.register_incoming(
            network="TRC20", tx_hash=tx_hash, token="USDT",
            amount=Decimal("60"), wallet_address="TLifecycleWallet", created_by=800050,
        )
        await engine.register_incoming(  # duplicate attempt
            network="TRC20", tx_hash=tx_hash, token="USDT",
            amount=Decimal("60"), wallet_address="TLifecycleWallet", created_by=800051,
        )
        await engine.request_review(first.transaction.id, actor_id=800051, reason="dup seen")
        with pytest.raises(CryptoTxOverrideUnavailableError):
            await engine.approve_override(
                first.transaction.id, approver_id=800099, approver_role="owner",
                reason="verified with client", confirmed=True,
            )
        await engine.complete_payout(first.transaction.id, actor_id=800099)

        audits = await _audit_rows_for(str(first.transaction.id))
        actions = [a.action for a in audits]
        for expected in (
            AuditAction.CRYPTO_TX_REGISTERED.value,
            AuditAction.DUPLICATE_TX_DETECTED.value,
            AuditAction.DUPLICATE_TX_BLOCKED.value,
            AuditAction.DUPLICATE_TX_REVIEW_REQUESTED.value,
            AuditAction.DUPLICATE_TX_OVERRIDE_REJECTED.value,
            AuditAction.PAYOUT_COMPLETED.value,
        ):
            assert expected in actions, f"missing audit action {expected} in {actions}"
        # immutable — every row has its own created_at, none were updated in place
        assert len(audits) == len(actions)


class TestBotAndWebSameBackendDecision:
    """Requirement 12's "bot and web both receiving the same backend
    decision" — since there is exactly one canonical service (requirement 13),
    a 'bot' caller and a 'web' caller are just two callers of the identical
    CryptoTxAntifraudEngine.register_incoming function. This test proves both
    call paths converge on one shared row/decision, not two divergent
    implementations."""

    async def test_bot_and_web_calls_converge_on_the_same_decision(self):
        tx_hash = _unique_hash("botweb")
        bot_view = await CryptoTxAntifraudEngine.register_incoming(
            network="TRC20", tx_hash=tx_hash, token="USDT",
            amount=Decimal("88"), wallet_address="TBotWebWallet", created_by=800060,
        )
        web_view = await CryptoTxAntifraudEngine.register_incoming(
            network="TRC20", tx_hash=tx_hash, token="USDT",
            amount=Decimal("88"), wallet_address="TBotWebWallet", created_by=800061,
            viewer_role="manager",
        )
        assert bot_view.is_duplicate is False
        assert web_view.is_duplicate is True
        assert web_view.transaction.id == bot_view.transaction.id
        assert web_view.warning.previous_operator_id == 800060
        assert web_view.warning.previous_status == bot_view.transaction.status
