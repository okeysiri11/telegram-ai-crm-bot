"""Sprint 17 — immersive play-money casino tables, extra bets, round phase."""

from __future__ import annotations

import os

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

os.environ["CASINO_PERSISTENCE"] = "memory"

from applications.casino.api.register import register_casino_routes
from applications.casino.engine import casino_engine
from applications.casino.roulette import payout_multiplier, settle_bet
from applications.casino.tables import DEFAULT_LIVE_ROOM_ID, live_room_id
from applications.casino.tenant import bind_casino_tenant

AUTH = {"Authorization": "Bearer test"}


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


def test_extra_bet_types_and_payouts():
    assert payout_multiplier("low") == 1
    assert payout_multiplier("dozen_1") == 2
    assert payout_multiplier("column_1") == 2
    assert settle_bet(bet_type="low", numbers=[], amount_chips=10, result_number=5) == 20
    assert settle_bet(bet_type="low", numbers=[], amount_chips=10, result_number=20) == 0
    assert settle_bet(bet_type="dozen_3", numbers=[], amount_chips=10, result_number=25) == 30
    assert settle_bet(bet_type="column_1", numbers=[], amount_chips=10, result_number=1) == 30


def test_live_table_aliases():
    assert live_room_id("roulette-royale") == DEFAULT_LIVE_ROOM_ID
    assert live_room_id("roulette-royale-1") == DEFAULT_LIVE_ROOM_ID


async def test_lobby_tables_and_phase(client: TestClient):
    lobby = await (await client.get("/api/casino/v1/lobby")).json()
    assert lobby["city_entry"]["route"] == "/casino"
    names = [t["table"] for t in lobby["roulette_tables"]]
    assert "Roulette Royale 1" in names
    opened = await client.post("/api/casino/v1/venues/odessa-prime/roulette/rounds", headers=AUTH)
    body = await opened.json()
    assert body["phase"] in {"BETTING_OPEN", "BETTING_CLOSING", "NO_MORE_BETS"}
    assert body["server_authoritative"] is True
    assert "result_number" in body


async def test_dozen_bet_and_authoritative_spin(client: TestClient):
    opened = await client.post("/api/casino/v1/venues/odessa-prime/roulette/rounds", headers=AUTH)
    round_id = (await opened.json())["round_id"]
    placed = await client.post(
        f"/api/casino/v1/roulette/rounds/{round_id}/bets",
        headers=AUTH,
        json={"bet_type": "dozen_1", "amount_chips": 10, "idempotency_key": "s17-d1"},
    )
    assert placed.status == 201
    spin = await client.post(f"/api/casino/v1/roulette/rounds/{round_id}/spin", headers=AUTH)
    result = await spin.json()
    assert result["settled"] is True
    assert result["phase"] == "SETTLED"
    again = await client.post(f"/api/casino/v1/roulette/rounds/{round_id}/spin", headers=AUTH)
    dup = await again.json()
    assert dup["result_number"] == result["result_number"]
    assert dup["duplicate_settlement_guard"] is True


async def test_join_royale_one(client: TestClient):
    join = await client.post(
        "/api/casino/v1/venues/odessa-prime/rooms/roulette-royale-1/join",
        headers=AUTH,
    )
    assert join.status == 200
    body = await join.json()
    assert body["table"] == "Roulette Royale 1"
    assert body["min_bet"] == 10
    legacy = await client.post("/api/casino/v1/venues/odessa-prime/rooms/join", headers=AUTH)
    assert (await legacy.json())["reconnected"] is True
