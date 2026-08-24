"""Sprint AUTO 1.5 — director analytics, cash flow, completeness, tenant isolation."""

from __future__ import annotations

import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.auto_enterprise.api.register import register_auto_enterprise_routes
from services.auto_ops import reset_auto_ops_for_tests
from services.auto_ops.analytics_catalog import forecast_profit, recommend_price_cut

OPS = "/api/auto-ops/v1"
VIN_SOLD = "1HGCM82633A004352"
VIN_HOLD = "WBAFR9C50DD123456"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_auto_enterprise_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_ops():
    reset_auto_ops_for_tests()
    yield
    reset_auto_ops_for_tests()


def _hdr(org: str, role: str = "auto_director", principal: str | None = None) -> dict[str, str]:
    h = {"X-Organization-Id": org, "X-Role": role}
    if principal:
        h["X-Principal"] = principal
    return h


async def _vehicle(client: TestClient, org: str, vin: str, **body) -> str:
    payload = {"vin": vin, "manufacturer": "BMW", "model": "X5", "year": 2013, **body}
    res = await client.post(f"{OPS}/vehicles", json=payload, headers=_hdr(org))
    assert res.status == 201, await res.text()
    return (await res.json())["item"]["id"]


async def test_health_is_auto_1_5(client: TestClient):
    res = await client.get(f"{OPS}/health")
    body = await res.json()
    assert body["sprint"] in {"AUTO_1.5", "AUTO_1.6", "AUTO_1.7", "AUTO_1.8", "AUTO_1.8.5"}
    assert "Новый бот не строится" in body["telegram"]["message_ru"]
    assert body["telegram"]["implemented"] is True
    intents = {i["command"] for i in body["telegram"]["intents"]}
    assert "/report" in intents
    assert "/cashflow" in intents


def test_forecast_and_price_cut_are_deterministic():
    fc = forecast_profit(invested=36200, remaining=0, expected_sale=40900)
    assert fc["label_ru"] == "ПРОГНОЗ"
    assert fc["actual"] is False
    assert fc["forecast_profit"] == 4700
    rec = recommend_price_cut(cost=36200, current_price=42500, target_price=40900)
    assert rec["cost"] == 36200
    assert rec["target_price"] == 40900
    assert rec["target_margin_pct"] is not None


async def test_cost_profit_margin_fx_completeness_and_ranking(client: TestClient):
    org = f"auto-a15-{uuid.uuid4().hex[:8]}"
    sold_id = await _vehicle(client, org, VIN_SOLD, status="PURCHASED", purchase_date="2026-07-01", purchase_price=18000)
    hold_id = await _vehicle(client, org, VIN_HOLD, status="READY_FOR_SALE", purchase_date="2026-06-01", purchase_price=20000, sale_price_expected=28000)
    await client.post(f"{OPS}/expenses", json={"vehicle_id": sold_id, "category": "PURCHASE", "amount": 18000, "currency": "USD", "payment_status": "paid"}, headers=_hdr(org))
    await client.post(f"{OPS}/expenses", json={"vehicle_id": sold_id, "category": "SEA_FREIGHT", "amount": 1000, "currency": "EUR", "exchange_rate": 1.1, "payment_status": "paid"}, headers=_hdr(org))
    await client.post(f"{OPS}/expenses", json={"vehicle_id": sold_id, "category": "IMPORT_VAT", "amount": 4000, "currency": "USD", "payment_status": "paid"}, headers=_hdr(org))
    await client.post(f"{OPS}/expenses", json={"vehicle_id": sold_id, "category": "REPAIR", "amount": 800, "currency": "USD", "payment_status": "paid"}, headers=_hdr(org))
    await client.post(f"{OPS}/vehicles/{sold_id}", json={"status": "SOLD", "sale_price_actual": 28000, "sale_date": "2026-08-01"}, headers=_hdr(org))
    await client.post(f"{OPS}/expenses", json={"vehicle_id": hold_id, "category": "PURCHASE", "amount": 20000, "currency": "USD", "payment_status": "paid"}, headers=_hdr(org))
    await client.post(f"{OPS}/expenses", json={"vehicle_id": hold_id, "category": "SEA_FREIGHT", "amount": 1500, "currency": "USD", "payment_status": "planned"}, headers=_hdr(org))

    eco = await (await client.get(f"{OPS}/analytics/economics", headers=_hdr(org))).json()
    by_vin = {r["vin"]: r for r in eco["items"]}
    sold = by_vin[VIN_SOLD]
    hold = by_vin[VIN_HOLD]
    assert sold["purchase"] == 18000
    assert sold["logistics"] == 1100
    assert sold["customs"] == 4000
    assert sold["repair"] == 800
    assert sold["cost"] == 23900
    assert sold["profit"] == 4100
    assert sold["sold"] is True
    assert hold["sold"] is False
    assert hold["profit"] is None
    assert hold["forecast"]["label_ru"] == "ПРОГНОЗ"
    assert hold["forecast"]["forecast_total_cost"] == 21500
    assert "брокера" in (hold["completeness_note_ru"] or "") or hold["quality"] != "KNOWN"

    rank = await (await client.get(f"{OPS}/analytics/ranking", headers=_hdr(org))).json()
    strong_vins = {r["vin"] for r in rank["strongest"]}
    assert VIN_SOLD in strong_vins
    assert VIN_HOLD not in strong_vins
    forecast_vins = {r["vin"] for r in rank["unsold_forecast"]}
    assert VIN_HOLD in forecast_vins

    mgr = await client.get(f"{OPS}/analytics/ranking", headers=_hdr(org, "auto_manager"))
    assert mgr.status == 403
    mgr_eco = await (await client.get(f"{OPS}/analytics/economics", headers=_hdr(org, "auto_manager"))).json()
    assert mgr_eco["ok"] is True
    assert mgr_eco["items"][0].get("finance_restricted") is True
    assert "profit" not in mgr_eco["items"][0] or mgr_eco["items"][0].get("finance_restricted")


async def test_cashflow_does_not_invent_balance_and_detects_gap(client: TestClient):
    org = f"auto-a15-{uuid.uuid4().hex[:8]}"
    vid = await _vehicle(client, org, VIN_SOLD, status="PURCHASED")
    await client.post(
        f"{OPS}/expenses",
        json={"vehicle_id": vid, "category": "SEA_FREIGHT", "amount": 25000, "currency": "USD", "payment_status": "planned", "payment_date": "2026-09-15"},
        headers=_hdr(org),
    )
    empty = await (await client.get(f"{OPS}/analytics/cashflow", headers=_hdr(org))).json()
    assert empty["opening_known"] is False
    assert empty["gap"] is None
    assert empty["items"][0]["running_balance"] is None

    acc = await client.post(f"{OPS}/finance/accounts", json={"account_type": "BANK_USD", "balance": 5000, "source": "WEB"}, headers=_hdr(org))
    assert acc.status in {200, 201}, await acc.text()
    gap = await (await client.get(f"{OPS}/analytics/cashflow", headers=_hdr(org))).json()
    assert gap["opening_known"] is True
    assert gap["gap"] is not None
    assert "кассовый разрыв" in gap["gap"]["message_ru"].lower()
    assert gap["items"][0]["running_balance"] < 0

    mgr = await client.get(f"{OPS}/finance/accounts", headers=_hdr(org, "auto_manager"))
    assert mgr.status == 403


async def test_receivables_repair_variance_tenant_isolation_and_export(client: TestClient):
    org = f"auto-a15-{uuid.uuid4().hex[:8]}"
    other = f"auto-a15-{uuid.uuid4().hex[:8]}"
    vid = await _vehicle(client, org, VIN_SOLD, status="PREPARATION")
    await _vehicle(client, other, VIN_SOLD, status="SOLD", purchase_price=99999)
    cid = (await (await client.post(f"{OPS}/clients", json={"name": "Петров", "phone": "+380501110011"}, headers=_hdr(org, "auto_manager"))).json())["item"]["id"]
    deal = await client.post(
        f"{OPS}/crm/deals",
        json={"client_id": cid, "vehicle_id": vid, "sale_price": 30000, "due_at": "2020-01-01", "assigned_manager_id": "mgr-a"},
        headers=_hdr(org, "auto_manager"),
    )
    assert deal.status == 201, await deal.text()
    did = (await deal.json())["item"]["id"]
    await client.post(f"{OPS}/crm/receipts", json={"deal_id": did, "vehicle_id": vid, "client_id": cid, "amount": 5000, "status": "confirmed"}, headers=_hdr(org))
    recv = await (await client.get(f"{OPS}/analytics/receivables", headers=_hdr(org))).json()
    assert recv["summary"]["total_owed"] == 25000
    assert recv["summary"]["overdue"] == 25000
    isolated = await (await client.get(f"{OPS}/analytics/receivables", headers=_hdr(other))).json()
    assert isolated["summary"]["total_owed"] == 0

    await client.post(f"{OPS}/expenses", json={"vehicle_id": vid, "category": "REPAIR", "amount": 1000, "payment_status": "planned"}, headers=_hdr(org))
    await client.post(f"{OPS}/expenses", json={"vehicle_id": vid, "category": "REPAIR", "amount": 1800, "payment_status": "paid"}, headers=_hdr(org))
    repair = await (await client.get(f"{OPS}/analytics/repair", headers=_hdr(org))).json()
    row = next(r for r in repair["items"] if r["vehicle_id"] == vid)
    assert row["budget_exceeded"] is True
    assert row["planned_repair"] == 1000
    assert row["actual_repair"] == 1800

    eco_a = await (await client.get(f"{OPS}/analytics/economics", headers=_hdr(org))).json()
    eco_b = await (await client.get(f"{OPS}/analytics/economics", headers=_hdr(other))).json()
    assert eco_a["total"] == 1
    assert eco_b["total"] == 1
    assert eco_a["items"][0]["id"] != eco_b["items"][0]["id"]

    export = await client.get(f"{OPS}/analytics/export?kind=economics&format=csv", headers=_hdr(org))
    assert export.status == 200
    assert "csv" in export.content_type
    text = (await export.read()).decode("utf-8")
    assert "VIN" in text or VIN_SOLD in text

    demo_denied = await client.post(f"{OPS}/analytics/demo", json={}, headers=_hdr(org))
    assert demo_denied.status == 400
    demo = await client.post(f"{OPS}/analytics/demo", json={"confirm_demo": True}, headers=_hdr(org))
    assert demo.status in {200, 201}
    body = await demo.json()
    assert body["is_demo"] is True
    assert len(body["items"]) >= 8


async def test_director_report_and_lifecycle_history(client: TestClient):
    org = f"auto-a15-{uuid.uuid4().hex[:8]}"
    await _vehicle(client, org, VIN_SOLD, status="PURCHASED")
    director = await (await client.get(f"{OPS}/analytics/director", headers=_hdr(org))).json()
    assert director["ok"] is True
    assert "автомобил" in director["summary_ru"].lower()
    assert director["sprint"] in {"AUTO_1.5", "AUTO_1.6", "AUTO_1.7", "AUTO_1.8", "AUTO_1.8.5"}
    funnel = await (await client.get(f"{OPS}/analytics/funnel", headers=_hdr(org))).json()
    purchased = next(s for s in funnel["items"] if s["id"] == "purchased")
    assert purchased["count"] == 1
    assert purchased["duration_quality"] in {"KNOWN", "UNKNOWN"}

    bind = await client.post(f"{OPS}/telegram/members", json={"telegram_id": 51001, "role": "auto_director", "label": "Директор"}, headers=_hdr(org))
    assert bind.status in {200, 201}
    report = await client.post(f"{OPS}/telegram/inbound", json={"telegram_id": 51001, "text": "/report"}, headers=_hdr(org))
    body = await report.json()
    assert report.status == 200
    assert "сводка" in body["message_ru"].lower()
    labels = [b["text"] for row in body["keyboard"] for b in row]
    assert "Открыть аналитику" in labels
    assert "Cash Flow" in labels
    mgr_dir = await (await client.get(f"{OPS}/analytics/director", headers=_hdr(org, "auto_manager"))).json()
    assert mgr_dir.get("restricted") is True
    assert "прибыль скрыта" in mgr_dir["summary_ru"].lower()
