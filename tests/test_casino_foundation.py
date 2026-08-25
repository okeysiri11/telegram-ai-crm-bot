"""Sprint 15 — play-money casino foundation."""

from __future__ import annotations

import os

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

os.environ["CASINO_PERSISTENCE"] = "memory"

from applications.casino.api.register import register_casino_routes
from applications.casino.engine import casino_engine
from applications.casino.roulette import color_for_number, settle_bet, spin_european
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


def test_server_spin_never_accepts_client_number():
    first = spin_european()
    second = spin_european()
    assert 0 <= first["number"] <= 36
    assert first["color"] == color_for_number(first["number"])
    assert first["entropy_hex"] != second["entropy_hex"]
    assert first["server_authoritative"] is True


def test_roulette_payouts():
    assert settle_bet(bet_type="red", numbers=[], amount_chips=10, result_number=1) == 20
    assert settle_bet(bet_type="red", numbers=[], amount_chips=10, result_number=2) == 0
    assert settle_bet(bet_type="straight", numbers=[17], amount_chips=10, result_number=17) == 360
    assert settle_bet(bet_type="straight", numbers=[17], amount_chips=10, result_number=0) == 0


async def test_lobby_venues_and_city_binding(client: TestClient):
    health = await client.get("/api/casino/v1/health")
    assert health.status == 200
    body = await health.json()
    assert body["play_money_only"] is True
    assert body["real_money_implemented"] is False
    assert "password" not in str(body).lower()
    lobby = await client.get("/api/casino/v1/lobby")
    assert lobby.status == 200
    payload = await lobby.json()
    assert payload["city_entry"]["building_id"] == "casino"
    assert payload["city_entry"]["venue_route"] == "/casino/venues/odessa-prime"
    venues = await client.get("/api/casino/v1/venues?q=odessa")
    assert venues.status == 200
    items = (await venues.json())["items"]
    assert any(v["venue_id"] == "odessa-prime" for v in items)
    venue = await client.get("/api/casino/v1/venues/odessa-prime")
    assert venue.status == 200
    assert (await venue.json())["city_building_id"] == "casino"


async def test_auth_gates_and_wallet_ledger(client: TestClient):
    assert (await client.get("/api/casino/v1/wallet")).status == 401
    assert (await client.post("/api/casino/v1/venues/odessa-prime/roulette/rounds")).status == 401
    wallet = await client.get("/api/casino/v1/wallet", headers=AUTH)
    assert wallet.status == 200
    data = await wallet.json()
    assert data["balance_chips"] == 10_000
    assert data["play_money_only"] is True
    ledger = await client.get("/api/casino/v1/ledger", headers=AUTH)
    assert ledger.status == 200
    assert (await ledger.json())["items"]


async def test_tenant_isolation(client: TestClient):
    await client.get("/api/casino/v1/wallet", headers=AUTH)
    other = await client.get("/api/casino/v1/wallet", headers=AUTH_B)
    a = await (await client.get("/api/casino/v1/wallet", headers=AUTH)).json()
    b = await other.json()
    assert a["tenant_id"] == "default"
    assert b["tenant_id"] == "tenant-b"
    assert a["wallet_id"] != b["wallet_id"]


async def test_roulette_demo_duplicate_settlement_and_wager_validation(client: TestClient):
    opened = await client.post("/api/casino/v1/venues/odessa-prime/roulette/rounds", headers=AUTH)
    assert opened.status == 201
    round_id = (await opened.json())["round_id"]
    bad = await client.post(
        f"/api/casino/v1/roulette/rounds/{round_id}/bets",
        headers=AUTH,
        json={"bet_type": "red", "amount_chips": 10, "result_number": 17},
    )
    assert bad.status == 400
    too_big = await client.post(
        f"/api/casino/v1/roulette/rounds/{round_id}/bets",
        headers=AUTH,
        json={"bet_type": "red", "amount_chips": 99_999},
    )
    assert too_big.status == 400
    placed = await client.post(
        f"/api/casino/v1/roulette/rounds/{round_id}/bets",
        headers=AUTH,
        json={"bet_type": "red", "amount_chips": 10, "idempotency_key": "k1"},
    )
    assert placed.status == 201
    again = await client.post(
        f"/api/casino/v1/roulette/rounds/{round_id}/bets",
        headers=AUTH,
        json={"bet_type": "red", "amount_chips": 10, "idempotency_key": "k1"},
    )
    assert again.status == 201
    assert (await placed.json())["bet_id"] == (await again.json())["bet_id"]
    spin = await client.post(
        f"/api/casino/v1/roulette/rounds/{round_id}/spin",
        headers=AUTH,
        json={"result_number": 1},
    )
    assert spin.status == 400
    first = await client.post(f"/api/casino/v1/roulette/rounds/{round_id}/spin", headers=AUTH)
    assert first.status == 200
    result = await first.json()
    assert result["settled"] is True
    assert result["server_authoritative"] is True
    number = result["result_number"]
    second = await client.post(f"/api/casino/v1/roulette/rounds/{round_id}/spin", headers=AUTH)
    assert second.status == 200
    dup = await second.json()
    assert dup["result_number"] == number
    assert dup["duplicate_settlement_guard"] is True
    wallet = await (await client.get("/api/casino/v1/wallet", headers=AUTH)).json()
    # One 10-chip wager; win credits 20, loss stays 9990.
    assert wallet["balance_chips"] in {9990, 10010}


async def test_multiplayer_room_foundation(client: TestClient):
    join = await client.post("/api/casino/v1/venues/odessa-prime/rooms/join", headers=AUTH)
    assert join.status == 200
    body = await join.json()
    assert body["count"] >= 1
    room = await client.get("/api/casino/v1/venues/odessa-prime/rooms")
    assert room.status == 200
    leave = await client.post("/api/casino/v1/venues/odessa-prime/rooms/leave", headers=AUTH)
    assert leave.status == 200
