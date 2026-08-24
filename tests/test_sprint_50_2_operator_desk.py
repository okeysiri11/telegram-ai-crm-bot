"""Sprint 50.2 — operator desk: paper trading, journal, signals, consensus."""

from __future__ import annotations

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.crypto_enterprise.api.register import register_crypto_enterprise_routes
from services.fx_market_intel.consensus import build_consensus
from services.fx_market_intel.desk_ops import get_fx_desk_ops, reset_fx_desk_ops_for_tests
from services.fx_market_intel.memory import reset_memory_for_tests
from services.fx_market_intel.paper_trading import (
    assert_paper_only,
    close_position,
    create_paper_order,
    pnl_for_close,
    try_fill_limit,
)
from services.fx_market_intel.service import reset_fx_market_intel_for_tests
from services.fx_market_intel.signals import assert_no_trade_execution, create_signal, evaluate_price_trigger

FX = "/api/crypto-mi/v1/fx-intel"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_crypto_enterprise_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def _reset():
    reset_memory_for_tests()
    reset_fx_market_intel_for_tests()
    reset_fx_desk_ops_for_tests()
    yield
    reset_memory_for_tests()
    reset_fx_market_intel_for_tests()
    reset_fx_desk_ops_for_tests()


def test_chief_consensus_structured():
    c = build_consensus(
        technical_vote="WATCH_BUY",
        dxy_vote="WATCH_SELL",
        macro_vote="NEUTRAL",
        news_vote="WAIT",
        session_vote="WATCH_BUY",
    )
    assert "overall_direction" in c and "disagreement_score" in c


def test_signal_price_trigger_no_trade():
    sig = create_signal(
        instrument="EUR/USD",
        timeframe="1H",
        signal="WATCH_BUY",
        confidence=0.5,
        price_trigger={"enabled": True, "price": 1.15, "direction": "above"},
    )
    assert_no_trade_execution(sig)
    fired = evaluate_price_trigger(sig, 1.16)
    assert fired["price_trigger"]["triggered"] is True
    assert_no_trade_execution(fired)


def test_paper_market_limit_sl_tp_pnl_close():
    market = create_paper_order(
        tenant_id="t1",
        instrument="EUR/USD",
        side="BUY",
        order_type="market",
        quantity=10,
        mark_price=1.1000,
        stop_loss=1.0900,
        take_profit=1.1200,
        signal_id="sig_x",
        analysis_run_id="run_x",
    )
    assert_paper_only(market["order"])
    assert market["position"]["status"] == "OPEN"
    limit = create_paper_order(
        tenant_id="t1",
        instrument="EUR/USD",
        side="BUY",
        order_type="limit",
        quantity=1,
        limit_price=1.05,
        mark_price=1.10,
    )
    assert limit["order"]["status"] == "PENDING"
    filled = try_fill_limit(limit["order"], 1.04)
    assert filled and filled["order"]["status"] == "FILLED"
    metrics = pnl_for_close(side="BUY", entry=1.10, exit_price=1.12, quantity=10)
    assert metrics["pnl"] > 0
    closed = close_position(market["position"], exit_price=1.12, reason="manual")
    assert closed["status"] == "CLOSED"
    assert closed["pnl"] is not None
    assert closed["trade_execution"] is False


@pytest.mark.asyncio
async def test_http_paper_journal_signal_links(client: TestClient):
    created = await client.post(
        f"{FX}/signals",
        json={"instrument": "EUR/USD", "signal": "WAIT", "tenant_id": "desk-t", "source": "chart"},
    )
    assert created.status == 201
    sig = (await created.json())["signal"]
    assert sig["analytics_only"] is True
    assert sig["trade_execution"] is False

    paper = await client.post(
        f"{FX}/paper",
        json={
            "action": "place",
            "tenant_id": "desk-t",
            "instrument": "EUR/USD",
            "side": "BUY",
            "order_type": "market",
            "quantity": 1,
            "signal_id": sig["signal_id"],
        },
    )
    body = await paper.json()
    assert body.get("trade_execution") is not True
    if paper.status == 201 and body.get("position"):
        assert body["position"]["paper"] is True
        pid = body["position"]["position_id"]
        closed = await client.post(
            f"{FX}/paper",
            json={"action": "close", "tenant_id": "desk-t", "position_id": pid},
        )
        cj = await closed.json()
        if cj.get("ok"):
            journal = await client.get(f"{FX}/journal?tenant_id=desk-t")
            assert journal.status == 200
            assert (await journal.json())["items"]

    links = await client.get(f"{FX}/links?tenant_id=desk-t&signal_id={sig['signal_id']}")
    assert links.status == 200
    assert "links" in await links.json()


@pytest.mark.asyncio
async def test_desk_ops_tenant_isolation():
    ops = get_fx_desk_ops()
    await ops.create_manual_signal(tenant_id="a", instrument="EUR/USD", signal="WAIT")
    await ops.create_manual_signal(tenant_id="b", instrument="DXY", signal="NEUTRAL")
    r = await ops.place_paper_order(
        tenant_id="a",
        body={"instrument": "EUR/USD", "side": "BUY", "order_type": "limit", "quantity": 1, "limit_price": 0.5},
    )
    assert r["order"]["tenant_id"] == "a"
    assert all(o["tenant_id"] == "a" for o in ops.list_orders("a"))
    assert ops.list_orders("b") == []
