"""Sprint 18 — blackjack, slots, presence, tenant isolation, result authority."""

from __future__ import annotations

import os

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

os.environ["CASINO_PERSISTENCE"] = "memory"

from applications.casino.api.register import register_casino_routes
from applications.casino.blackjack import hand_total, is_blackjack, new_hand, settle_outcome
from applications.casino.engine import casino_engine
from applications.casino.slots import evaluate, spin_reels
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


def test_blackjack_deck_authority_and_settlement_math():
    hand = new_hand(player_id="p", venue_id="odessa-prime", wager=100, hand_id="bj_x")
    assert len(hand["player_cards"]) == 2
    assert len(hand["dealer_cards"]) == 2
    assert "shoe" in hand
    player = [{"rank": "A", "suit": "s"}, {"rank": "K", "suit": "h"}]
    dealer = [{"rank": "9", "suit": "c"}, {"rank": "7", "suit": "d"}]
    assert is_blackjack(player) is True
    settled = settle_outcome(player=player, dealer=dealer, wager=100)
    assert settled["payout_chips"] == 250
    assert settled["server_authoritative"] is True
    bust = settle_outcome(
        player=[{"rank": "K", "suit": "s"}, {"rank": "K", "suit": "h"}, {"rank": "5", "suit": "d"}],
        dealer=[{"rank": "9", "suit": "c"}, {"rank": "7", "suit": "d"}],
        wager=50,
    )
    assert bust["outcome"] == "lose"
    assert bust["payout_chips"] == 0
    assert hand_total([{"rank": "A", "suit": "s"}, {"rank": "9", "suit": "h"}]) == 20


def test_slot_result_authority_local():
    grid = spin_reels()
    assert len(grid) == 5
    assert all(len(col) == 3 for col in grid)
    result = evaluate([["CHERRY"] * 3] * 5, 10)
    assert result["payout_chips"] > 0
    assert result["server_authoritative"] is True


async def test_lobby_opens_blackjack_and_slots(client: TestClient):
    lobby = await (await client.get("/api/casino/v1/lobby")).json()
    ids = {g["id"] for g in lobby["games"]}
    assert ids >= {"roulette", "blackjack", "slots"}
    floor = {a["id"]: a for a in lobby["floor"]}
    assert floor["blackjack"]["coming_soon"] is False
    assert floor["slots"]["coming_soon"] is False
    assert floor["blackjack"]["route"] == "/casino/rooms/blackjack"
    assert any(t["table"] == "Odessa Gold" for t in lobby["slot_machines"])
    health = await (await client.get("/api/casino/v1/health")).json()
    assert health["application_version"] == "19.0.0-play-money"
    assert floor["poker"]["route"] == "/casino/rooms/poker"
    assert floor["vip"]["coming_soon"] is False


async def test_roulette_result_authority_and_duplicate(client: TestClient):
    opened = await client.post("/api/casino/v1/venues/odessa-prime/roulette/rounds", headers=AUTH)
    round_id = (await opened.json())["round_id"]
    denied = await client.post(
        f"/api/casino/v1/roulette/rounds/{round_id}/spin",
        headers=AUTH,
        json={"result_number": 17},
    )
    assert denied.status == 400
    await client.post(
        f"/api/casino/v1/roulette/rounds/{round_id}/bets",
        headers=AUTH,
        json={"bet_type": "red", "amount_chips": 10, "idempotency_key": "s18-r"},
    )
    first = await (await client.post(f"/api/casino/v1/roulette/rounds/{round_id}/spin", headers=AUTH)).json()
    second = await (await client.post(f"/api/casino/v1/roulette/rounds/{round_id}/spin", headers=AUTH)).json()
    assert first["result_number"] == second["result_number"]
    assert second["duplicate_settlement_guard"] is True


async def test_blackjack_server_authority_replay_and_auth(client: TestClient):
    assert (await client.post("/api/casino/v1/venues/odessa-prime/blackjack/hands")).status == 401
    denied = await client.post(
        "/api/casino/v1/venues/odessa-prime/blackjack/hands",
        headers=AUTH,
        json={"amount_chips": 50, "player_cards": [{"rank": "A", "suit": "s"}]},
    )
    assert denied.status == 400
    too_big = await client.post(
        "/api/casino/v1/venues/odessa-prime/blackjack/hands",
        headers=AUTH,
        json={"amount_chips": 99_999, "idempotency_key": "s18-bj-big"},
    )
    assert too_big.status == 400
    dealt = await client.post(
        "/api/casino/v1/venues/odessa-prime/blackjack/hands",
        headers=AUTH,
        json={"amount_chips": 50, "idempotency_key": "s18-bj"},
    )
    assert dealt.status == 201
    hand = await dealt.json()
    assert hand["server_authoritative"] is True
    assert "shoe" not in hand
    assert hand["dealer_cards"][1].get("hidden") or hand["settled"] is True
    replay = await client.post(
        "/api/casino/v1/venues/odessa-prime/blackjack/hands",
        headers=AUTH,
        json={"amount_chips": 50, "idempotency_key": "s18-bj"},
    )
    assert replay.status == 201
    assert (await replay.json())["hand_id"] == hand["hand_id"]
    if not hand["settled"]:
        fake = await client.post(
            f"/api/casino/v1/blackjack/hands/{hand['hand_id']}/stand",
            headers=AUTH,
            json={"dealer_cards": [{"rank": "2", "suit": "s"}]},
        )
        assert fake.status == 400
        stood = await client.post(
            f"/api/casino/v1/blackjack/hands/{hand['hand_id']}/stand",
            headers=AUTH,
            json={},
        )
        assert stood.status == 200
        body = await stood.json()
        assert body["settled"] is True
        assert body["settlement"]["server_authoritative"] is True
        again = await client.post(
            f"/api/casino/v1/blackjack/hands/{hand['hand_id']}/stand",
            headers=AUTH,
            json={},
        )
        dup = await again.json()
        assert dup["settlement"]["payout_chips"] == body["settlement"]["payout_chips"]
    wallet = await (await client.get("/api/casino/v1/wallet", headers=AUTH)).json()
    if hand["settled"]:
        assert isinstance(wallet["balance_chips"], int)
    else:
        outcome = body["settlement"]["outcome"]
        if outcome != "push":
            assert wallet["balance_chips"] != 10_000
    ledger = await (await client.get("/api/casino/v1/ledger", headers=AUTH)).json()
    assert any(row["reference_type"] == "blackjack" for row in ledger["items"])


async def test_slot_authority_settlement_idempotency_and_invalid_wager(client: TestClient):
    assert (
        await client.post("/api/casino/v1/venues/odessa-prime/slots/odessa-gold/spin")
    ).status == 401
    fake = await client.post(
        "/api/casino/v1/venues/odessa-prime/slots/odessa-gold/spin",
        headers=AUTH,
        json={"amount_chips": 10, "reels": [["SEVEN"] * 3] * 5},
    )
    assert fake.status == 400
    bad = await client.post(
        "/api/casino/v1/venues/odessa-prime/slots/odessa-gold/spin",
        headers=AUTH,
        json={"amount_chips": 0, "idempotency_key": "s18-slot-0"},
    )
    assert bad.status == 400
    first = await client.post(
        "/api/casino/v1/venues/odessa-prime/slots/odessa-gold/spin",
        headers=AUTH,
        json={"amount_chips": 10, "idempotency_key": "s18-slot"},
    )
    assert first.status == 200
    spin = await first.json()
    assert spin["server_authoritative"] is True
    assert spin["machine"] == "odessa-gold"
    assert len(spin["reels"]) == 5
    second = await client.post(
        "/api/casino/v1/venues/odessa-prime/slots/odessa-gold/spin",
        headers=AUTH,
        json={"amount_chips": 10, "idempotency_key": "s18-slot"},
    )
    dup = await second.json()
    assert dup["reels"] == spin["reels"]
    assert dup["payout_chips"] == spin["payout_chips"]
    wallet = await (await client.get("/api/casino/v1/wallet", headers=AUTH)).json()
    expected = 10_000 - 10 + int(spin["payout_chips"])
    assert wallet["balance_chips"] == expected
    ledger = await (await client.get("/api/casino/v1/ledger", headers=AUTH)).json()
    assert any(row["reference_type"] == "slots" for row in ledger["items"])


async def test_tenant_isolation_wallet_and_sessions(client: TestClient):
    await client.post(
        "/api/casino/v1/venues/odessa-prime/slots/odessa-gold/spin",
        headers=AUTH,
        json={"amount_chips": 25, "idempotency_key": "s18-iso"},
    )
    a = await (await client.get("/api/casino/v1/wallet", headers=AUTH)).json()
    b = await (await client.get("/api/casino/v1/wallet", headers=AUTH_B)).json()
    assert a["tenant_id"] != b["tenant_id"]
    assert a["balance_chips"] != b["balance_chips"]
    assert b["balance_chips"] == 10_000


async def test_presence_live_blackjack_and_slots(client: TestClient):
    bj = await client.post(
        "/api/casino/v1/venues/odessa-prime/rooms/blackjack-salon/join",
        headers=AUTH,
    )
    assert bj.status == 200
    slots = await client.post(
        "/api/casino/v1/venues/odessa-prime/rooms/slots-odessa-gold/join",
        headers=AUTH,
    )
    assert slots.status == 200
    assert (await slots.json())["table"] == "Odessa Gold"
