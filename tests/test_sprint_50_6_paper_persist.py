"""Sprint 50.6 — durable paper hydrate, SL/TP validation, open journal, idempotency."""

from __future__ import annotations

import pytest

from services.fx_market_intel.desk_ops import get_fx_desk_ops, reset_fx_desk_ops_for_tests
from services.fx_market_intel.journal import journal_position_opened
from services.fx_market_intel.paper_trading import create_paper_order, validate_sl_tp_vs_side


@pytest.fixture(autouse=True)
def _reset_ops():
    reset_fx_desk_ops_for_tests()
    yield
    reset_fx_desk_ops_for_tests()


def test_validate_sl_tp_buy_sell():
    assert validate_sl_tp_vs_side(side="BUY", entry=1.1, stop_loss=1.09, take_profit=1.12)["ok"]
    bad = validate_sl_tp_vs_side(side="BUY", entry=1.1, stop_loss=1.11, take_profit=1.12)
    assert bad["ok"] is False
    assert "ниже" in bad["message_ru"]
    bad2 = validate_sl_tp_vs_side(side="SELL", entry=1.1, stop_loss=1.09, take_profit=1.08)
    assert bad2["ok"] is False
    assert "выше" in bad2["message_ru"]


def test_market_order_status_filled_and_open_journal():
    r = create_paper_order(
        tenant_id="t506",
        instrument="EUR/USD",
        side="BUY",
        order_type="MARKET",
        quantity=1,
        mark_price=1.085,
        stop_loss=1.08,
        take_profit=1.09,
    )
    assert r["order"]["status"] == "FILLED"
    assert r["position"]["status"] == "OPEN"
    j = journal_position_opened(r["position"], r["order"])
    assert j["event"] == "PAPER_POSITION_OPENED"
    assert j["journal_id"].startswith("jn_")


@pytest.mark.asyncio
async def test_place_open_close_lifecycle_memory():
    ops = get_fx_desk_ops()
    import uuid

    async def _fake_mark(instrument: str):
        return 1.0850

    ops._mark = _fake_mark  # type: ignore[method-assign]
    idem = f"life-{uuid.uuid4().hex}"

    placed = await ops.place_paper_order(
        tenant_id="t506-life",
        body={
            "instrument": "EUR/USD",
            "side": "BUY",
            "order_type": "MARKET",
            "quantity": 1,
            "stop_loss": 1.08,
            "take_profit": 1.09,
            "idempotency_key": idem,
        },
    )
    assert placed["ok"] is True
    assert placed["order"]["status"] == "FILLED"
    assert placed["position"]["status"] == "OPEN"
    assert placed["journal"]["event"] == "PAPER_POSITION_OPENED"
    pid = placed["position"]["position_id"]
    oid = placed["order"]["order_id"]

    replay = await ops.place_paper_order(
        tenant_id="t506-life",
        body={
            "instrument": "EUR/USD",
            "side": "BUY",
            "order_type": "MARKET",
            "quantity": 1,
            "idempotency_key": idem,
        },
    )
    assert replay.get("idempotent_replay") is True
    assert len([o for o in ops.list_orders("t506-life") if o.get("order_id") == oid]) == 1

    assert any(p["position_id"] == pid and p["status"] == "OPEN" for p in ops.list_positions("t506-life"))
    assert any(o["order_id"] == oid and o["status"] == "FILLED" for o in ops.list_orders("t506-life"))
    assert any(j.get("event") == "PAPER_POSITION_OPENED" for j in ops.list_journal("t506-life"))
    assert any("открыта" in str(n.get("title") or "") for n in ops.list_notifications("t506-life"))

    closed = await ops.close_paper_position(tenant_id="t506-life", position_id=pid)
    assert closed["ok"] is True
    assert closed["position"]["status"] == "CLOSED"
    assert closed["journal"]["event"] == "PAPER_POSITION_CLOSED"
    assert not any(p["position_id"] == pid and p["status"] == "OPEN" for p in ops.list_positions("t506-life"))
    acc = ops.get_account("t506-life")
    assert int(acc.get("trades_count") or 0) >= 1
    assert any("закрыта" in str(n.get("title") or "").lower() for n in ops.list_notifications("t506-life"))


@pytest.mark.asyncio
async def test_invalid_sl_surfaces_russian_error():
    ops = get_fx_desk_ops()

    async def _fake_mark(instrument: str):
        return 1.0850

    ops._mark = _fake_mark  # type: ignore[method-assign]
    bad = await ops.place_paper_order(
        tenant_id="t506-sl",
        body={"instrument": "EUR/USD", "side": "BUY", "order_type": "MARKET", "quantity": 1, "stop_loss": 1.09},
    )
    assert bad["ok"] is False
    assert "Stop Loss" in str(bad.get("message_ru"))


@pytest.mark.asyncio
async def test_hydrate_merges_db_payload_into_empty_memory(monkeypatch):
    """Simulate DB rows restoring into a fresh desk ops instance."""
    reset_fx_desk_ops_for_tests()
    ops = get_fx_desk_ops()

    class _Row:
        def __init__(self, **kw):
            for k, v in kw.items():
                setattr(self, k, v)

    order_payload = {
        "order_id": "po_hydrate1",
        "tenant_id": "hyd",
        "instrument": "EUR/USD",
        "side": "BUY",
        "order_type": "MARKET",
        "quantity": 1,
        "status": "FILLED",
        "fill_price": 1.08,
        "created_at": "2026-08-12T00:00:00+00:00",
        "paper": True,
        "trade_execution": False,
    }
    pos_payload = {
        "position_id": "pp_hydrate1",
        "order_id": "po_hydrate1",
        "tenant_id": "hyd",
        "instrument": "EUR/USD",
        "side": "BUY",
        "quantity": 1,
        "entry_price": 1.08,
        "status": "OPEN",
        "opened_at": "2026-08-12T00:00:00+00:00",
        "paper": True,
        "trade_execution": False,
    }
    jn_payload = {
        "journal_id": "jn_hydrate1",
        "tenant_id": "hyd",
        "event": "PAPER_POSITION_OPENED",
        "instrument": "EUR/USD",
        "entry": 1.08,
        "created_at": "2026-08-12T00:00:01+00:00",
        "paper": True,
    }

    class _Repo:
        def __init__(self, session):
            pass

        async def list_paper_orders(self, tenant_id, *, limit=200):
            return [_Row(order_key="po_hydrate1", payload=order_payload, status="FILLED", instrument="EUR/USD", side="BUY", fill_price=1.08)]

        async def list_paper_positions(self, tenant_id, *, limit=200):
            return [
                _Row(
                    position_key="pp_hydrate1",
                    order_key="po_hydrate1",
                    payload=pos_payload,
                    status="OPEN",
                    instrument="EUR/USD",
                    side="BUY",
                    entry_price=1.08,
                    exit_price=None,
                    pnl=None,
                    stop_loss=None,
                    take_profit=None,
                )
            ]

        async def list_journal_entries(self, tenant_id, *, limit=200):
            return [_Row(journal_key="jn_hydrate1", payload=jn_payload, instrument="EUR/USD", entry_price=1.08, exit_price=None, pnl=None)]

    class _SessionCtx:
        async def __aenter__(self):
            return object()

        async def __aexit__(self, *a):
            return False

    monkeypatch.setattr("database.session.get_session", lambda: _SessionCtx())
    monkeypatch.setattr("repositories.fx_market_intel_repository.FxMarketIntelRepository", _Repo)

    await ops.ensure_hydrated("hyd")
    assert any(o["order_id"] == "po_hydrate1" for o in ops.list_orders("hyd"))
    assert any(p["position_id"] == "pp_hydrate1" and p["status"] == "OPEN" for p in ops.list_positions("hyd"))
    assert any(j["journal_id"] == "jn_hydrate1" for j in ops.list_journal("hyd"))
    # second call is no-op
    await ops.ensure_hydrated("hyd")
    assert len(ops.list_orders("hyd")) == 1
