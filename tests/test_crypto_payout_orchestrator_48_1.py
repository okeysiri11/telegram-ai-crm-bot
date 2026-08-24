"""
Sprint 48.1 — Crypto/OTC canonical payout orchestration (security-critical).

Covers what Sprint 48.0's engine-level tests (test_crypto_tx_antifraud_48_0.py)
could not: the real, deal-scoped payout path — CryptoPayoutOrchestrator
sitting above the legacy crypto_deals/crypto_payments persistence
(database_legacy.py) and below Telegram/Web, exactly as both must call it.

Why these tests fake the legacy persistence layer instead of exercising real
SQLite (discovered while writing this file, not assumed): tests/conftest.py
line 12 unconditionally sets POSTGRES_ONLY=true for the entire test session
("Tests always use PostgreSQL policy; SQLite must not bootstrap") — under
that flag database_legacy.py's module-level `conn`/`cursor` are `None` for
every test, always, regardless of what any individual test does. This is a
deliberate, pre-existing repo policy, not something Sprint 48.1 introduced;
no test file before this one has ever called a database_legacy.py crypto
function, so there was no precedent to preserve either way. Sprint 46.6's
RESULT doc records the same resolution for a different module ("mocking out
the one incidental DB call") — this file follows that established pattern:
a small, faithful in-memory fake standing in for the real sqlite functions,
patched onto the actual `database_legacy` module object so the orchestrator's
`from database import ...` calls (which resolve through database/__init__.py
's __getattr__ shim to whatever `database_legacy.<name>` currently is) pick
up the fake transparently. What IS real and unmocked: the Postgres-backed
CryptoTxAntifraudEngine/CryptoTxRegistryRepository and the actual DB unique
constraint — the fake only replaces the legacy *deal/payment* bookkeeping,
which is exactly the boundary services/crypto_payout_orchestrator.py itself
draws (see its module docstring).
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest

import database.models.automotive_partner_integration  # noqa: F401
import database.models.deal_engine_v1  # noqa: F401
import database.models.lead_engine  # noqa: F401
import database.models.partner_tenant_engine  # noqa: F401
import database.models.payment_engine_v1  # noqa: F401
import database.models.user_role  # noqa: F401
import database.models.role  # noqa: F401
import database.models.role_permission  # noqa: F401
import database.models.users  # noqa: F401

from database.models.audit_log import AuditAction, AuditLog
from database.models.crypto_tx_registry import CryptoTxStatus
from services.crypto_payout_orchestrator import (
    CryptoDealInvalidStateError,
    CryptoDealNotFoundError,
    CryptoPayoutOrchestrator,
    CryptoPayoutResultStatus,
)
from services.pg_crypto_tx_antifraud_engine import (
    CryptoTxOverrideDeniedError,
    CryptoTxOverrideUnavailableError,
)

pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
async def _reset_db_engine_per_test():
    """Same rationale as test_crypto_tx_antifraud_48_0.py's fixture of the
    same name — real Postgres engine, one event loop per test function.
    Disposes before AND after (Sprint 48.1 fix — see that file's fixture
    docstring for why "after only" isn't enough across a full suite run)."""
    from database.session import shutdown_db

    await shutdown_db()
    yield
    await shutdown_db()


class _FakeLegacyCryptoStore:
    """In-memory stand-in for database_legacy.py's crypto_deals/
    crypto_payments tables — see module docstring for why. Row shapes match
    the real SELECT * column order exactly (verified against
    database_legacy.py::get_crypto_deal / format_crypto_deal_text's unpack
    and this sprint's own get_crypto_payment_for_deal)."""

    def __init__(self) -> None:
        self._deals: dict[int, list] = {}
        self._payments: dict[int, list] = {}
        self._next_deal_id = 1
        self._next_payment_id = 1

    def create_deal(self, *, client_id: int | None = None) -> int:
        client_id = client_id or (700000 + uuid.uuid4().int % 100000)
        deal_id = self._next_deal_id
        self._next_deal_id += 1
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        # id, client_id, request_id, direction, asset, amount, currency,
        # rate, fee, manager_id, status, payment_status, created_at,
        # updated_at, closed_at, notes
        self._deals[deal_id] = [
            deal_id, client_id, None, "BUY_USDT", "USDT", 1000.0, "USD",
            1.0, 0.0, client_id, "PAYMENT_PENDING", "WAITING_PAYMENT",
            now, now, None, None,
        ]
        self._create_payment(deal_id, client_id, 1000.0, "USD")
        return deal_id

    def _create_payment(self, deal_id: int, created_by: int, amount, currency: str) -> int:
        payment_id = self._next_payment_id
        self._next_payment_id += 1
        # id, deal_id, amount, currency, payment_status, created_by, confirmed_at, delivered_at
        self._payments[payment_id] = [
            payment_id, deal_id, amount, currency, "WAITING_PAYMENT", created_by, None, None,
        ]
        return payment_id

    def get_crypto_deal(self, deal_id: int):
        row = self._deals.get(deal_id)
        return tuple(row) if row else None

    def get_crypto_payment_for_deal(self, deal_id: int):
        for row in reversed(list(self._payments.values())):
            if row[1] == deal_id:
                return tuple(row)
        return None

    def create_crypto_payment(self, deal_id: int, created_by: int, amount=None, currency: str = "USD") -> int:
        return self._create_payment(deal_id, created_by, amount, currency)

    def update_crypto_payment_status(self, payment_id: int, payment_status: str, actor_id: int) -> bool:
        row = self._payments.get(payment_id)
        if not row:
            return False
        row[4] = payment_status
        deal_row = self._deals.get(row[1])
        if deal_row is not None:
            deal_row[11] = payment_status
            if payment_status == "PAYMENT_RECEIVED":
                deal_row[10] = "PROCESSING"
        return True

    def update_crypto_deal_status(self, deal_id: int, status: str, actor_id: int) -> bool:
        row = self._deals.get(deal_id)
        if not row:
            return False
        row[10] = status
        return True


@pytest.fixture
def legacy_store(monkeypatch):
    store = _FakeLegacyCryptoStore()
    import database_legacy as legacy

    monkeypatch.setattr(legacy, "get_crypto_deal", store.get_crypto_deal)
    monkeypatch.setattr(legacy, "get_crypto_payment_for_deal", store.get_crypto_payment_for_deal)
    monkeypatch.setattr(legacy, "create_crypto_payment", store.create_crypto_payment)
    monkeypatch.setattr(legacy, "update_crypto_payment_status", store.update_crypto_payment_status)
    monkeypatch.setattr(legacy, "update_crypto_deal_status", store.update_crypto_deal_status)
    return store


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


class TestFirstPayoutConfirmed:
    async def test_first_payout_allowed_and_transitions_legacy_state(self, legacy_store):
        deal_id = legacy_store.create_deal()
        tx_hash = _unique_hash("payout_first")

        result = await CryptoPayoutOrchestrator.confirm_payout(
            deal_id=deal_id, network="TRC20", tx_hash=tx_hash, token="USDT",
            amount=Decimal("1000"), wallet_address="TPayoutWallet",
            actor_id=800100, actor_role="manager",
        )
        assert result.status == CryptoPayoutResultStatus.CONFIRMED
        assert result.transaction.status == CryptoTxStatus.COMPLETED.value
        assert result.deal_id == deal_id

        # the existing canonical legacy transition actually ran
        deal = legacy_store.get_crypto_deal(deal_id)
        assert deal[11] == "PAYMENT_RECEIVED"  # payment_status column

        audits = await _audit_rows_for(str(result.transaction.id))
        actions = {a.action for a in audits}
        assert AuditAction.CRYPTO_TX_REGISTERED.value in actions
        assert AuditAction.PAYOUT_COMPLETED.value in actions


class TestDuplicatePayoutBlocked:
    async def test_duplicate_payout_blocks_before_legacy_state_transition(self, legacy_store):
        deal_a = legacy_store.create_deal()
        deal_b = legacy_store.create_deal()
        tx_hash = _unique_hash("payout_dup")

        first = await CryptoPayoutOrchestrator.confirm_payout(
            deal_id=deal_a, network="TRC20", tx_hash=tx_hash, token="USDT",
            amount=Decimal("500"), wallet_address="TDupWallet",
            actor_id=800101, actor_role="operator",
        )
        assert first.status == CryptoPayoutResultStatus.CONFIRMED

        # a SECOND, unrelated deal tries to reuse the same tx_hash — this is
        # the actual fraud scenario the sprint protects against.
        second = await CryptoPayoutOrchestrator.confirm_payout(
            deal_id=deal_b, network="TRC20", tx_hash=tx_hash, token="USDT",
            amount=Decimal("500"), wallet_address="TDupWallet",
            actor_id=800102, actor_role="operator",
        )
        assert second.status == CryptoPayoutResultStatus.DUPLICATE
        assert second.warning is not None
        assert second.warning.previous_legacy_deal_id == deal_a

        # STOP means STOP: deal_b's payment must NOT have transitioned.
        deal_b_row = legacy_store.get_crypto_deal(deal_b)
        assert deal_b_row[11] == "WAITING_PAYMENT"


class TestConcurrentDuplicateRace:
    async def test_two_deals_racing_same_tx_hash_exactly_one_confirmed(self, legacy_store):
        deal_a = legacy_store.create_deal()
        deal_b = legacy_store.create_deal()
        tx_hash = _unique_hash("payout_race")

        results = await asyncio.gather(
            CryptoPayoutOrchestrator.confirm_payout(
                deal_id=deal_a, network="TRC20", tx_hash=tx_hash, token="USDT",
                amount=Decimal("10"), wallet_address="TRaceWallet",
                actor_id=800103, actor_role="operator",
            ),
            CryptoPayoutOrchestrator.confirm_payout(
                deal_id=deal_b, network="TRC20", tx_hash=tx_hash, token="USDT",
                amount=Decimal("10"), wallet_address="TRaceWallet",
                actor_id=800104, actor_role="operator",
            ),
        )
        confirmed = [r for r in results if r.status == CryptoPayoutResultStatus.CONFIRMED]
        duplicates = [r for r in results if r.status == CryptoPayoutResultStatus.DUPLICATE]
        assert len(confirmed) == 1
        assert len(duplicates) == 1

        winner_deal_id = confirmed[0].deal_id
        loser_deal_id = deal_a if winner_deal_id == deal_b else deal_b
        assert legacy_store.get_crypto_deal(winner_deal_id)[11] == "PAYMENT_RECEIVED"
        assert legacy_store.get_crypto_deal(loser_deal_id)[11] == "WAITING_PAYMENT"


class TestIdempotentRetry:
    async def test_retrying_the_same_confirmation_is_idempotent(self, legacy_store):
        deal_id = legacy_store.create_deal()
        tx_hash = _unique_hash("payout_retry")

        first = await CryptoPayoutOrchestrator.confirm_payout(
            deal_id=deal_id, network="TRC20", tx_hash=tx_hash, token="USDT",
            amount=Decimal("20"), wallet_address="TRetryWallet",
            actor_id=800105, actor_role="operator",
        )
        assert first.status == CryptoPayoutResultStatus.CONFIRMED

        # operator double-taps "confirm" (or the bot resends after a
        # timeout) — same deal, same tx_hash. Must NOT be treated as fraud.
        retry = await CryptoPayoutOrchestrator.confirm_payout(
            deal_id=deal_id, network="TRC20", tx_hash=tx_hash, token="USDT",
            amount=Decimal("20"), wallet_address="TRetryWallet",
            actor_id=800105, actor_role="operator",
        )
        assert retry.status == CryptoPayoutResultStatus.ALREADY_CONFIRMED
        assert retry.transaction.id == first.transaction.id

        # side effects did not re-execute: exactly one PAYOUT_COMPLETED audit row
        audits = await _audit_rows_for(str(first.transaction.id))
        completions = [a for a in audits if a.action == AuditAction.PAYOUT_COMPLETED.value]
        assert len(completions) == 1


class TestLegacyReferenceIntegrity:
    async def test_legacy_deal_and_payment_reference_set_and_never_overwritten(self, legacy_store):
        deal_id = legacy_store.create_deal()
        tx_hash = _unique_hash("payout_refs")

        result = await CryptoPayoutOrchestrator.confirm_payout(
            deal_id=deal_id, network="TRC20", tx_hash=tx_hash, token="USDT",
            amount=Decimal("30"), wallet_address="TRefWallet",
            actor_id=800106, actor_role="operator",
        )
        assert result.transaction.legacy_deal_id == deal_id
        assert result.transaction.legacy_payment_id == result.payment_id
        original_payment_id = result.transaction.legacy_payment_id

        # idempotent retry must not alter the stored reference
        retry = await CryptoPayoutOrchestrator.confirm_payout(
            deal_id=deal_id, network="TRC20", tx_hash=tx_hash, token="USDT",
            amount=Decimal("30"), wallet_address="TRefWallet",
            actor_id=800106, actor_role="operator",
        )
        assert retry.transaction.legacy_deal_id == deal_id
        assert retry.transaction.legacy_payment_id == original_payment_id


class TestDealValidation:
    async def test_nonexistent_deal_raises_not_found(self, legacy_store):
        with pytest.raises(CryptoDealNotFoundError):
            await CryptoPayoutOrchestrator.confirm_payout(
                deal_id=999_999_999, network="TRC20", tx_hash=_unique_hash("missing"),
                token="USDT", amount=Decimal("1"), wallet_address="W",
                actor_id=800107, actor_role="operator",
            )

    async def test_terminal_deal_state_rejects_new_payout(self, legacy_store):
        deal_id = legacy_store.create_deal()
        legacy_store.update_crypto_deal_status(deal_id, "CANCELLED", 800108)

        with pytest.raises(CryptoDealInvalidStateError):
            await CryptoPayoutOrchestrator.confirm_payout(
                deal_id=deal_id, network="TRC20", tx_hash=_unique_hash("terminal"),
                token="USDT", amount=Decimal("1"), wallet_address="W",
                actor_id=800108, actor_role="operator",
            )


class TestOverrideThroughOrchestrator:
    async def test_unauthorized_override_rejected(self, legacy_store):
        deal_id = legacy_store.create_deal()
        tx_hash = _unique_hash("orch_unauth")
        await CryptoPayoutOrchestrator.confirm_payout(
            deal_id=deal_id, network="TRC20", tx_hash=tx_hash, token="USDT",
            amount=Decimal("1"), wallet_address="W", actor_id=800109, actor_role="operator",
        )
        deal_id_2 = legacy_store.create_deal()
        dup = await CryptoPayoutOrchestrator.confirm_payout(
            deal_id=deal_id_2, network="TRC20", tx_hash=tx_hash, token="USDT",
            amount=Decimal("1"), wallet_address="W", actor_id=800110, actor_role="operator",
        )
        assert dup.status == CryptoPayoutResultStatus.DUPLICATE

        with pytest.raises(CryptoTxOverrideDeniedError):
            await CryptoPayoutOrchestrator.approve_override(
                dup.transaction.id, approver_id=800110, approver_role="operator",
                reason="please", confirmed=True,
            )

    async def test_override_unavailable_without_real_reauth(self, legacy_store):
        deal_id = legacy_store.create_deal()
        tx_hash = _unique_hash("orch_unavailable")
        await CryptoPayoutOrchestrator.confirm_payout(
            deal_id=deal_id, network="TRC20", tx_hash=tx_hash, token="USDT",
            amount=Decimal("1"), wallet_address="W", actor_id=800111, actor_role="operator",
        )
        deal_id_2 = legacy_store.create_deal()
        dup = await CryptoPayoutOrchestrator.confirm_payout(
            deal_id=deal_id_2, network="TRC20", tx_hash=tx_hash, token="USDT",
            amount=Decimal("1"), wallet_address="W", actor_id=800112, actor_role="operator",
        )
        with pytest.raises(CryptoTxOverrideUnavailableError):
            await CryptoPayoutOrchestrator.approve_override(
                dup.transaction.id, approver_id=800112, approver_role="owner",
                reason="verified with client by phone", confirmed=True,
            )

    async def test_send_for_review_remains_available(self, legacy_store):
        deal_id = legacy_store.create_deal()
        tx_hash = _unique_hash("orch_review")
        await CryptoPayoutOrchestrator.confirm_payout(
            deal_id=deal_id, network="TRC20", tx_hash=tx_hash, token="USDT",
            amount=Decimal("1"), wallet_address="W", actor_id=800113, actor_role="operator",
        )
        deal_id_2 = legacy_store.create_deal()
        dup = await CryptoPayoutOrchestrator.confirm_payout(
            deal_id=deal_id_2, network="TRC20", tx_hash=tx_hash, token="USDT",
            amount=Decimal("1"), wallet_address="W", actor_id=800114, actor_role="operator",
        )
        reviewed = await CryptoPayoutOrchestrator.request_review(
            dup.transaction.id, actor_id=800114, reason="needs manual check"
        )
        assert reviewed.id == dup.transaction.id
        audits = await _audit_rows_for(str(dup.transaction.id))
        assert any(a.action == AuditAction.DUPLICATE_TX_REVIEW_REQUESTED.value for a in audits)


class TestTelegramRouterUsesOrchestratorOnly:
    """Architectural guarantee, not just behavioral: handlers.py/the bot
    router must not call CryptoTxAntifraudEngine directly for a payout
    decision — only CryptoPayoutOrchestrator. Verified by inspecting the
    actual imports of the shipped module, not by convention alone."""

    async def test_bot_router_does_not_import_the_raw_engine_class(self):
        import routers.crypto_tx_antifraud_router as bot_router

        assert not hasattr(bot_router, "CryptoTxAntifraudEngine")
        assert bot_router.CryptoPayoutOrchestrator is not None

    async def test_handlers_module_delegates_to_router_helper_not_orchestrator_directly(self):
        """handlers.py may only decide *when* to start the flow (a
        presentation concern) — the actual orchestrator call lives inside
        routers/crypto_tx_antifraud_router.py, not handlers.py."""
        import handlers

        assert handlers.start_payout_confirmation is not None
        assert not hasattr(handlers, "CryptoPayoutOrchestrator")


class TestManagementApiEndpoints:
    """Web's real, deal-scoped surface — platform_management/
    crypto_tx_antifraud_routes.py — proven end to end over real HTTP, not by
    calling Python functions directly."""

    @pytest.fixture
    def app(self):
        from aiohttp import web as aioweb

        from platform_management.crypto_tx_antifraud_routes import register_crypto_tx_antifraud_routes

        application = aioweb.Application()
        register_crypto_tx_antifraud_routes(application)
        return application

    @pytest.fixture
    async def client(self, app):
        from aiohttp.test_utils import TestClient, TestServer

        async with TestClient(TestServer(app)) as test_client:
            yield test_client

    async def test_deal_summary_reflects_real_legacy_deal(self, client, auth_headers, legacy_store):
        deal_id = legacy_store.create_deal()
        resp = await client.get(f"/management/v1/crypto-tx/deals/{deal_id}", headers=auth_headers)
        assert resp.status == 200
        body = await resp.json()
        assert body["data"]["can_confirm_payout"] is True
        assert body["data"]["payment_status"] == "WAITING_PAYMENT"

    async def test_confirm_payout_then_duplicate_via_http(self, client, auth_headers, legacy_store):
        deal_a = legacy_store.create_deal()
        deal_b = legacy_store.create_deal()
        tx_hash = _unique_hash("http_payout")
        payload_a = {
            "network": "TRC20", "tx_hash": tx_hash, "token": "USDT",
            "amount": "123.45", "wallet_address": "THttpWallet",
        }
        first = await client.post(
            f"/management/v1/crypto-tx/deals/{deal_a}/confirm-payout", json=payload_a, headers=auth_headers
        )
        assert first.status == 200
        first_body = await first.json()
        assert first_body["data"]["status"] == "confirmed"

        second = await client.post(
            f"/management/v1/crypto-tx/deals/{deal_b}/confirm-payout", json=payload_a, headers=auth_headers
        )
        assert second.status == 409
        second_body = await second.json()
        assert second_body["data"]["status"] == "duplicate"
        assert second_body["data"]["warning"]["tx_hash"] == tx_hash

    async def test_direct_bypass_register_endpoint_no_longer_exists(self, client, auth_headers):
        """Sprint 48.0 had a generic POST /crypto-tx/register that let a
        caller claim a tx_hash with no deal validation at all — a direct-API
        bypass of the orchestrator. Sprint 48.1 removed it; this asserts it
        stays removed."""
        resp = await client.post(
            "/management/v1/crypto-tx/register",
            json={"network": "TRC20", "tx_hash": "x", "token": "USDT", "amount": "1", "wallet_address": "W"},
            headers=auth_headers,
        )
        assert resp.status == 404

    async def test_override_requires_owner_role_at_http_layer(self, client, api_key_headers):
        """api_key_headers (tests/conftest.py) issues scopes without
        management.admin/owner — proves the require_role(OWNER) gate on the
        HTTP endpoint rejects insufficiently-privileged callers before the
        request reaches the orchestrator/engine at all."""
        resp = await client.post(
            "/management/v1/crypto-tx/00000000-0000-0000-0000-000000000000/override/approve",
            json={"reason": "test", "confirmed": True},
            headers=api_key_headers,
        )
        assert resp.status == 403

    async def test_override_unavailable_at_http_layer_for_owner(self, client, auth_headers, legacy_store):
        """Even a genuine OWNER-level caller gets 503 (service unavailable),
        never a fabricated success — proves the "do not fake reauth" rule
        holds all the way through the HTTP layer, not just in the engine's
        own unit tests."""
        deal_a = legacy_store.create_deal()
        deal_b = legacy_store.create_deal()
        tx_hash = _unique_hash("http_override_unavail")
        await client.post(
            f"/management/v1/crypto-tx/deals/{deal_a}/confirm-payout",
            json={"network": "TRC20", "tx_hash": tx_hash, "token": "USDT", "amount": "1", "wallet_address": "W"},
            headers=auth_headers,
        )
        dup = await client.post(
            f"/management/v1/crypto-tx/deals/{deal_b}/confirm-payout",
            json={"network": "TRC20", "tx_hash": tx_hash, "token": "USDT", "amount": "1", "wallet_address": "W"},
            headers=auth_headers,
        )
        dup_body = await dup.json()
        tx_id = dup_body["data"]["transaction"]["id"]

        resp = await client.post(
            f"/management/v1/crypto-tx/{tx_id}/override/approve",
            json={"reason": "verified", "confirmed": True},
            headers=auth_headers,
        )
        assert resp.status == 503
