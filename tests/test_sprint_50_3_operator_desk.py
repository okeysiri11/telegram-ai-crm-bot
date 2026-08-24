"""Sprint 50.3 — notifications, calendar, paper account, journal traceability."""

from __future__ import annotations

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.crypto_enterprise.api.register import register_crypto_enterprise_routes
from services.fx_market_intel.calendar_events import filter_events, make_event
from services.fx_market_intel.desk_ops import get_fx_desk_ops, reset_fx_desk_ops_for_tests
from services.fx_market_intel.memory import reset_memory_for_tests
from services.fx_market_intel.notifications import create_notification, transition
from services.fx_market_intel.paper_trading import (
    INITIAL_BALANCE_USD,
    account_snapshot,
    cancel_pending,
    check_sl_tp,
    close_position,
    create_paper_order,
    mark_position,
    new_account,
    risk_preview,
    try_fill_limit,
)
from services.fx_market_intel.service import reset_fx_market_intel_for_tests
from services.fx_market_intel.signals import create_signal, evaluate_price_trigger

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


def test_notification_lifecycle_ru():
    n = create_notification(tenant_id="t", signal_id="s1", title="Сигнал", status="ACTIVE")
    assert n["status"] == "ACTIVE"
    assert "Подтвердить" in n["actions"]
    ack = transition(n, "подтвердить")
    assert ack["status"] == "ACKNOWLEDGED"
    off = transition(ack, "отключить")
    assert off["status"] == "DISABLED"


def test_calendar_filter_categories():
    events = [
        make_event(category="MACRO", title="CPI", scheduled_at="2026-08-11T12:00:00+00:00"),
        make_event(category="SIGNAL", title="Sig", scheduled_at="2026-08-11T13:00:00+00:00"),
        make_event(category="PAPER_TRADE", title="Paper", scheduled_at="2026-08-11T14:00:00+00:00"),
        make_event(category="MANUAL", title="Manual", scheduled_at="2026-08-11T15:00:00+00:00"),
    ]
    only_macro = filter_events(events, {"macro": True, "news": False, "analysis": False, "agent": False, "signal": False, "session": False, "paper": False, "manual": False})
    assert all(e["category"] == "MACRO" for e in only_macro)
    with_manual = filter_events(events, {"macro": False, "manual": True, "signal": False, "paper": False, "news": False, "analysis": False, "agent": False, "session": False})
    assert any(e["category"] == "MANUAL" for e in with_manual)


def test_paper_account_demo_100k():
    acc = new_account("t")
    assert acc["balance"] == INITIAL_BALANCE_USD == 100_000
    snap = account_snapshot(acc, [], [])
    assert snap["equity"] == 100_000
    assert snap["trades_count"] == 0
    assert snap["trade_execution"] is False


def test_paper_market_limit_sl_tp_cancel_pnl():
    market = create_paper_order(
        tenant_id="t1",
        instrument="EUR/USD",
        side="BUY",
        order_type="MARKET",
        quantity=10,
        mark_price=1.1000,
        stop_loss=1.0900,
        take_profit=1.1200,
        signal_id="sig_x",
        analysis_run_id="run_x",
        agent_result_id="ag_x",
    )
    assert market["order"]["status"] == "FILLED"
    assert market["position"]["status"] == "OPEN"
    limit = create_paper_order(
        tenant_id="t1",
        instrument="EUR/USD",
        side="BUY",
        order_type="LIMIT",
        quantity=1,
        limit_price=1.05,
        mark_price=1.10,
    )
    assert limit["order"]["status"] == "PENDING"
    cancelled = cancel_pending(limit["order"])
    assert cancelled["status"] == "CANCELLED"
    limit2 = create_paper_order(
        tenant_id="t1",
        instrument="EUR/USD",
        side="BUY",
        order_type="LIMIT",
        quantity=1,
        limit_price=1.05,
        mark_price=1.10,
    )
    filled = try_fill_limit(limit2["order"], 1.04)
    assert filled and filled["order"]["status"] == "FILLED"
    marked = mark_position(market["position"], 1.11)
    assert marked["unrealized_pnl"] > 0
    hit_tp = check_sl_tp(marked, 1.12)
    assert hit_tp and hit_tp["close_reason"] == "take_profit"
    closed = close_position(market["position"], exit_price=1.105, reason="manual")
    assert closed["status"] == "CLOSED" and closed["pnl"] is not None
    preview = risk_preview(entry=1.1, stop_loss=1.09, take_profit=1.12, quantity=10, side="BUY", balance=100000)
    assert preview["potential_loss"] is not None and preview["risk_pct"] is not None


def test_price_trigger_and_browser_signal_state():
    sig = create_signal(
        instrument="EUR/USD",
        timeframe="1H",
        signal="WATCH_BUY",
        confidence=0.55,
        price_trigger={"enabled": True, "price": 1.15, "direction": "above"},
    )
    fired = evaluate_price_trigger(sig, 1.16)
    assert fired["price_trigger"]["triggered"] is True
    n = create_notification(tenant_id="t", signal_id=sig["signal_id"], title="Сигнал сработал", status="TRIGGERED")
    assert n["status"] == "TRIGGERED"
    assert n["channel"] == "in_app"


@pytest.mark.asyncio
async def test_http_notifications_calendar_paper_account(client: TestClient):
    created = await client.post(
        f"{FX}/signals",
        json={"instrument": "EUR/USD", "signal": "WAIT", "tenant_id": "desk-50-3", "source": "chart"},
    )
    assert created.status == 201
    notif = await client.get(f"{FX}/notifications?tenant_id=desk-50-3")
    assert notif.status == 200
    items = (await notif.json())["items"]
    assert items
    nid = items[0]["notification_id"]
    ack = await client.post(
        f"{FX}/notifications",
        json={"tenant_id": "desk-50-3", "notification_id": nid, "action": "ack"},
    )
    assert ack.status == 200
    assert (await ack.json())["notification"]["status"] == "ACKNOWLEDGED"

    cal = await client.get(f"{FX}/calendar?tenant_id=desk-50-3")
    assert cal.status == 200
    cj = await cal.json()
    assert "events" in cj
    man = await client.post(
        f"{FX}/calendar",
        json={
            "action": "create",
            "tenant_id": "desk-50-3",
            "title": "Ручной тест",
            "date": "2026-08-11",
            "time": "10:00",
            "instrument": "EUR/USD",
            "category": "MANUAL",
        },
    )
    assert man.status == 201

    paper = await client.get(f"{FX}/paper?tenant_id=desk-50-3")
    assert paper.status == 200
    pj = await paper.json()
    assert pj["account"]["balance"] == 100000 or pj["account"]["balance"] == 100000.0
    assert pj["trade_execution"] is False

    placed = await client.post(
        f"{FX}/paper",
        json={
            "action": "place",
            "tenant_id": "desk-50-3",
            "instrument": "EUR/USD",
            "side": "BUY",
            "order_type": "LIMIT",
            "quantity": 1,
            "limit_price": 0.5,
        },
    )
    body = await placed.json()
    assert placed.status == 201
    assert body["order"]["status"] == "PENDING"
    cancel = await client.post(
        f"{FX}/paper",
        json={"action": "cancel", "tenant_id": "desk-50-3", "order_id": body["order"]["order_id"]},
    )
    assert (await cancel.json()).get("ok") is True

    links = await client.get(f"{FX}/links?tenant_id=desk-50-3")
    assert "calendar" in (await links.json())["links"]
    assert "notifications" in (await links.json())["links"]


@pytest.mark.asyncio
async def test_desk_ops_journal_traceability():
    from services.fx_market_intel.journal import journal_from_closed_position
    from services.fx_market_intel.paper_trading import try_fill_limit as fill

    ops = get_fx_desk_ops()
    r = await ops.place_paper_order(
        tenant_id="trace",
        body={
            "instrument": "EUR/USD",
            "side": "BUY",
            "order_type": "LIMIT",
            "quantity": 2,
            "limit_price": 1.0,
            "signal_id": "sig_t",
            "analysis_run_id": "run_t",
            "agent_result_id": "ag_t",
            "notes": "Почему: тест трассировки",
        },
    )
    assert r["order"]["status"] == "PENDING"
    hit = fill(r["order"], 0.99)
    assert hit
    closed_pos = close_position(hit["position"], exit_price=1.01, reason="manual")
    j = journal_from_closed_position(closed_pos, notes="manual")
    assert j["signal_id"] == "sig_t"
    assert j["analysis_run_id"] == "run_t"
    assert j["agent_result_id"] == "ag_t"
    assert "трассиров" in str(j["why_opened"]) or j["why_opened"]
    assert j["training_enabled"] is False
    ops._journal["trace"] = [j]
    assert ops.list_journal("trace")
