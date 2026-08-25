"""Sprint 16 — premium play-money casino UX, demo grant, presence, security."""

from __future__ import annotations

import os

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

os.environ["CASINO_PERSISTENCE"] = "memory"

from applications.casino.api.register import register_casino_routes
from applications.casino.config import DEFAULT_CONFIG
from applications.casino.engine import casino_engine
from applications.casino.identity import display_identity
from applications.casino.tenant import bind_casino_tenant

AUTH = {"Authorization": "Bearer test"}
AUTH_B = {"Authorization": "Bearer test", "X-Tenant-Id": "tenant-b"}


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_casino_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_casino():
    bind_casino_tenant("default")
    casino_engine.reset()
    yield
    casino_engine.reset()
    bind_casino_tenant("default")


def _blob(payload: object) -> str:
    return str(payload).lower()


async def test_casino_lobby_route_and_floor(client: TestClient):
    lobby = await client.get("/api/casino/v1/lobby")
    assert lobby.status == 200
    payload = await lobby.json()
    assert payload["play_money_only"] is True
    assert payload["real_money_implemented"] is False
    assert payload["currency_label"] == "PLAY"
    assert payload["display_currency"] == "DEMO CHIPS"
    assert payload["city_entry"]["enter_label"] == "Войти в казино"
    labels = {area["label"] for area in payload["floor"]}
    assert labels >= {"RECEPTION", "BAR", "ROULETTE", "BLACKJACK", "POKER", "SLOTS", "VIP"}
    roulette = next(a for a in payload["floor"] if a["id"] == "roulette")
    assert roulette["coming_soon"] is False
    soon = [a for a in payload["floor"] if a["id"] != "roulette"]
    assert all(a["status_label"] == "Скоро" for a in soon)
    games = await client.get("/api/casino/v1/games")
    assert games.status == 200
    assert any(item["id"] == "roulette" for item in (await games.json())["items"])


async def test_venue_binding_and_search(client: TestClient):
    venue = await client.get("/api/casino/v1/venues/odessa-prime")
    assert venue.status == 200
    body = await venue.json()
    assert body["city_building_id"] == "casino"
    assert body["city_route"] == "/casino/venues/odessa-prime"
    for query in ("казино", "odessa", "casino", "roulette"):
        found = await client.get(f"/api/casino/v1/venues?q={query}")
        assert found.status == 200
        items = (await found.json())["items"]
        assert any(v["venue_id"] == "odessa-prime" for v in items)


async def test_play_wallet_ledger_and_demo_grant(client: TestClient):
    assert (await client.post("/api/casino/v1/wallet/demo-grant")).status == 401
    wallet = await (await client.get("/api/casino/v1/wallet", headers=AUTH)).json()
    assert wallet["balance_chips"] == 10_000
    assert wallet["currency_label"] == "PLAY"
    assert wallet["display_currency"] == "DEMO CHIPS"
    assert "$" not in str(wallet)
    assert "€" not in str(wallet)
    assert wallet["demo_grant_available"] is True
    rejected = await client.post(
        "/api/casino/v1/wallet/demo-grant",
        headers=AUTH,
        json={"amount_chips": 999_999},
    )
    assert rejected.status == 400
    granted = await client.post("/api/casino/v1/wallet/demo-grant", headers=AUTH)
    assert granted.status == 200
    after = await granted.json()
    assert after["balance_chips"] == 15_000
    assert after["demo_grant_available"] is False
    cooldown = await client.post("/api/casino/v1/wallet/demo-grant", headers=AUTH)
    assert cooldown.status == 429
    retry = await cooldown.json()
    assert retry["retry_after_seconds"] >= 1
    still = await (await client.get("/api/casino/v1/wallet", headers=AUTH)).json()
    assert still["balance_chips"] == 15_000
    ledger = await (await client.get("/api/casino/v1/ledger", headers=AUTH)).json()
    items = ledger["items"]
    assert items
    grant_row = next(row for row in items if row["entry_type"] == "demo_grant")
    assert grant_row["operation"] == "Demo grant"
    assert grant_row["balance_delta"] == 5_000
    assert grant_row["resulting_balance"] == 15_000
    assert "player_id" not in grant_row
    assert "email" not in _blob(ledger)


async def test_roulette_demo_wager_and_duplicate_settlement(client: TestClient):
    await client.get("/api/casino/v1/wallet", headers=AUTH)
    opened = await client.post("/api/casino/v1/venues/odessa-prime/roulette/rounds", headers=AUTH)
    round_id = (await opened.json())["round_id"]
    placed = await client.post(
        f"/api/casino/v1/roulette/rounds/{round_id}/bets",
        headers=AUTH,
        json={"bet_type": "black", "amount_chips": 25, "idempotency_key": "s16-1"},
    )
    assert placed.status == 201
    first = await client.post(f"/api/casino/v1/roulette/rounds/{round_id}/spin", headers=AUTH)
    result = await first.json()
    assert result["server_authoritative"] is True
    assert result["settled"] is True
    assert 0 <= result["result_number"] <= 36
    second = await client.post(f"/api/casino/v1/roulette/rounds/{round_id}/spin", headers=AUTH)
    dup = await second.json()
    assert dup["result_number"] == result["result_number"]
    assert dup["duplicate_settlement_guard"] is True
    wallet = await (await client.get("/api/casino/v1/wallet", headers=AUTH)).json()
    assert wallet["balance_chips"] in {9_975, 10_025}
    ledger = await (await client.get("/api/casino/v1/ledger", headers=AUTH)).json()
    wager_row = next(row for row in ledger["items"] if row["entry_type"] == "wager")
    assert wager_row["wager"] == 25
    assert wager_row["balance_delta"] == -25
    assert "resulting_balance" in wager_row


async def test_presence_join_leave_reconnect_display_names(client: TestClient):
    join = await client.post("/api/casino/v1/venues/odessa-prime/rooms/join", headers=AUTH)
    assert join.status == 200
    body = await join.json()
    assert body["table"] == "Roulette Royale"
    assert body["count"] == 1
    assert body["seats_total"] == 6
    assert body["status_label"] in {"Идет прием ставок", "Ожидание игроков"}
    assert all("display_name" in player for player in body["players"])
    assert all(str(player["display_name"]).startswith("Player ") for player in body["players"])
    blob = _blob(body)
    assert "email" not in blob
    assert "bearer" not in blob
    assert "@" not in blob
    again = await client.post("/api/casino/v1/venues/odessa-prime/rooms/join", headers=AUTH)
    assert (await again.json())["reconnected"] is True
    rooms = await client.get("/api/casino/v1/venues/odessa-prime/rooms")
    listed = await rooms.json()
    assert listed["online_count"] >= 1
    assert any(t["room_id"] == "roulette-royale" for t in listed["tables"])
    named = await client.post(
        "/api/casino/v1/venues/odessa-prime/rooms/roulette-royale/join",
        headers=AUTH,
    )
    assert named.status == 200
    soon = await client.post(
        "/api/casino/v1/venues/odessa-prime/rooms/blackjack-salon/join",
        headers=AUTH,
    )
    assert soon.status == 400
    alias = await client.get("/api/casino/v1/rooms?venue_id=odessa-prime")
    assert alias.status == 200
    leave = await client.post("/api/casino/v1/venues/odessa-prime/rooms/leave", headers=AUTH)
    assert leave.status == 200
    assert (await leave.json())["count"] == 0


def test_display_identity_is_stable_and_non_sensitive():
    assert display_identity("user-a") == display_identity("user-a")
    assert display_identity("user-a") != display_identity("user-b")
    assert display_identity("user-a").startswith("Player ")
    assert "user-a" not in display_identity("user-a")


async def test_auth_security_tenant_isolation_no_secret_exposure(client: TestClient):
    assert (await client.get("/api/casino/v1/wallet")).status == 401
    assert (await client.post("/api/casino/v1/wallet/demo-grant")).status == 401
    await client.get("/api/casino/v1/wallet", headers=AUTH)
    await client.post("/api/casino/v1/wallet/demo-grant", headers=AUTH)
    other = await client.get("/api/casino/v1/wallet", headers=AUTH_B)
    a = await (await client.get("/api/casino/v1/wallet", headers=AUTH)).json()
    b = await other.json()
    assert a["tenant_id"] != b["tenant_id"]
    assert a["balance_chips"] == 15_000
    assert b["balance_chips"] == 10_000
    health = await (await client.get("/api/casino/v1/health")).json()
    blob = _blob({"health": health, "wallet": a})
    assert "bot_token" not in blob
    assert "database_url" not in blob
    assert "redis" not in blob or "credential" not in blob
    assert DEFAULT_CONFIG.play_money_only is True
    assert DEFAULT_CONFIG.real_money_implemented is False
    assert DEFAULT_CONFIG.payment_processing_implemented is False
