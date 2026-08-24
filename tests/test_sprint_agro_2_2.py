"""AGRO 2.2 — grain operation lifecycle. Extends agro-ops, no second subsystem."""

from __future__ import annotations

import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.agro_enterprise.api.register import register_agro_enterprise_routes
from services.agro_ops import reset_agro_ops_for_tests

OPS = "/api/agro-ops/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_agro_enterprise_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_ops():
    reset_agro_ops_for_tests()
    yield
    reset_agro_ops_for_tests()


def _hdr(org: str, role: str = "agro_director") -> dict[str, str]:
    return {"X-Organization-Id": org, "X-Role": role}


async def test_health_keeps_2_0_and_adds_ops_version(client: TestClient):
    body = await (await client.get(f"{OPS}/health")).json()
    assert body["sprint"] == "agro-2.0"
    assert body["ux_version"] == "AGRO_2_0"
    assert body["command_center"] == "AGRO_2_0"
    assert body["crm_version"] == "AGRO_2_1"
    assert body["ops_version"] == "AGRO_2_2"
    cats = body["catalogs"]
    assert any(s["id"] == "in_transit" for s in cats["operation_statuses"])
    assert "Пшеница" in cats["quality_profiles"]
    assert any(r["id"] == "agro_quality" for r in body["roles"])


async def test_weighing_formula_and_inconsistent_net(client: TestClient):
    org = f"org-a22-w-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    op = (await (await client.post(f"{OPS}/operations", json={"crop": "Пшеница", "planned_qty": 24.5}, headers=h)).json())["item"]
    resp = await client.post(f"{OPS}/operations/{op['id']}/weighing", json={"gross": 24820, "tare": 2000, "scale": "loading", "unit": "кг"}, headers=h)
    body = await resp.json()
    assert resp.status == 201
    assert body["item"]["net"] == 22820
    bad = await client.post(f"{OPS}/operations/{op['id']}/weighing", json={"gross": 24820, "tare": 2000, "net": 100, "scale": "receiving"}, headers=h)
    b2 = await bad.json()
    assert bad.status == 400
    assert "Нетто" in (b2.get("message_ru") or "")


async def test_weight_discrepancy_creates_exception_not_accusation(client: TestClient):
    org = f"org-a22-d-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    op = (await (await client.post(f"{OPS}/operations", json={"crop": "Пшеница", "planned_qty": 25, "weight_tolerance_pct": 0.5}, headers=h)).json())["item"]
    await client.post(f"{OPS}/operations/{op['id']}/weighing", json={"gross": 26820, "tare": 2000, "scale": "loading", "unit": "кг"}, headers=h)
    await client.post(f"{OPS}/operations/{op['id']}/weighing", json={"gross": 26610, "tare": 2000, "scale": "receiving", "unit": "кг"}, headers=h)
    card = await (await client.get(f"{OPS}/operations/{op['id']}?tab=exceptions", headers=h)).json()
    kinds = [e.get("kind") for e in card["items"]]
    assert "weight_discrepancy" in kinds
    detail = next(e for e in card["items"] if e.get("kind") == "weight_discrepancy")
    assert "не является обвинением" in (detail.get("detail") or "").lower()


async def test_quality_pass_fail_and_discount_audit(client: TestClient):
    org = f"org-a22-q-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    op = (await (await client.post(f"{OPS}/operations", json={"crop": "Пшеница", "planned_qty": 10, "price": 8500, "create_purchase": True}, headers=h)).json())["item"]
    good = await (await client.post(f"{OPS}/operations/{op['id']}/quality", json={"moisture": 13, "protein": 12, "foreign_matter": 1}, headers=h)).json()
    assert good["comparison"]["result"] == "PASS"
    fail = await (await client.post(f"{OPS}/operations/{op['id']}/quality", json={"moisture": 16, "protein": 10, "foreign_matter": 3}, headers=h)).json()
    assert fail["comparison"]["result"] == "FAIL"
    test_id = fail["item"]["id"]
    dec = await client.post(
        f"{OPS}/operations/{op['id']}/quality-decision",
        json={"quality_test_id": test_id, "decision": "discount", "reason": "влажность", "original_price": 8500, "adjustment": -150, "responsible": "director"},
        headers=h,
    )
    assert dec.status == 200
    body = await dec.json()
    assert body["item"]["accepted_price"] == 8350
    deal = await (await client.get(f"{OPS}/entities/deal/{op['purchase_deal_id']}", headers=h)).json()
    assert deal["item"]["accepted_price"] == 8350


async def test_critical_numeric_ledger_allocation_and_pnl(client: TestClient):
    org = f"org-a22-n-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    sup = (await (await client.post(f"{OPS}/entities/counterparty", json={"name": "Поставщик Зерно", "types": ["supplier"]}, headers=h)).json())["item"]
    buyer = (await (await client.post(f"{OPS}/entities/counterparty", json={"name": "Покупатель А", "types": ["buyer"]}, headers=h)).json())["item"]
    wh = (await (await client.post(f"{OPS}/entities/warehouse", json={"name": "Склад Южный"}, headers=h)).json())["item"]
    created = await (
        await client.post(
            f"{OPS}/operations",
            json={
                "crop": "Пшеница",
                "planned_qty": 500,
                "price": 8500,
                "currency": "UAH",
                "unit": "т",
                "supplier_id": sup["id"],
                "warehouse_id": wh["id"],
                "create_purchase": True,
                "load_place": "Одесская обл.",
                "dest_place": "Склад Южный",
            },
            headers=h,
        )
    ).json()
    op = created["item"]
    assert op["number"].startswith("AG-")
    oid = op["id"]

    await client.post(f"{OPS}/operations/{oid}/truck", json={"plate": "BH 1234 AA", "driver_name": "Иван", "planned_weight": 246}, headers=h)
    await client.post(f"{OPS}/operations/{oid}/weighing", json={"gross": 260, "tare": 14, "scale": "receiving", "unit": "т", "idempotency_key": "w1"}, headers=h)
    await client.post(f"{OPS}/operations/{oid}/weighing", json={"gross": 258, "tare": 12, "scale": "receiving", "unit": "т", "idempotency_key": "w2"}, headers=h)
    dup_w = await (await client.post(f"{OPS}/operations/{oid}/weighing", json={"gross": 260, "tare": 14, "scale": "receiving", "unit": "т", "idempotency_key": "w1"}, headers=h)).json()
    assert dup_w.get("idempotent") is True

    await client.post(f"{OPS}/operations/{oid}/quality", json={"moisture": 13.2, "protein": 12, "foreign_matter": 1.1}, headers=h)
    rec = await (await client.post(f"{OPS}/operations/{oid}/receive", json={}, headers=h)).json()
    assert rec["ok"] is True
    assert abs(rec["received_qty"] - 492) < 1e-6
    lot_id = rec["item"]["id"]
    assert str(rec["item"]["lot_number"]).startswith("LOT-")

    dup_r = await client.post(f"{OPS}/operations/{oid}/receive", json={}, headers=h)
    assert dup_r.status == 409

    proc = await (await client.post(f"{OPS}/operations/{oid}/process", json={"lot_id": lot_id, "input_qty": 492, "output_qty": 488, "process_type": "drying"}, headers=h)).json()
    assert proc["loss"] == 4
    assert proc["loss_kind"] == "drying"

    await client.post(f"{OPS}/operations/{oid}/expense", json={"amount": 20000, "category": "transport", "idempotency_key": "e1"}, headers=h)
    dup_e = await (await client.post(f"{OPS}/operations/{oid}/expense", json={"amount": 20000, "category": "transport", "idempotency_key": "e1"}, headers=h)).json()
    assert dup_e.get("idempotent") is True
    await client.post(f"{OPS}/operations/{oid}/expense", json={"amount": 8000, "category": "storage"}, headers=h)

    sale1 = await (
        await client.post(
            f"{OPS}/operations/{oid}/sale",
            json={"buyer_id": buyer["id"], "price": 10000, "ship": True, "allocations": [{"lot_id": lot_id, "quantity": 300}]},
            headers=h,
        )
    ).json()
    assert sale1["ok"] is True
    card = await (await client.get(f"{OPS}/operations/{oid}", headers=h)).json()
    item = card["item"]
    assert abs((item["received_qty"] or 0) - 492) < 1e-6
    assert abs((item["usable_qty"] or 0) - 488) < 1e-6
    assert abs((item["sold_qty"] or 0) - 300) < 1e-6
    assert abs((item["remaining_qty"] or 0) - 188) < 1e-6
    assert item["remaining_qty"] not in {200, 192, 500}

    sale2 = await (
        await client.post(
            f"{OPS}/operations/{oid}/sale",
            json={"buyer_id": buyer["id"], "price": 10000, "ship": True, "allocations": [{"lot_id": lot_id, "quantity": 100}]},
            headers=h,
        )
    ).json()
    assert sale2["ok"] is True
    card = await (await client.get(f"{OPS}/operations/{oid}", headers=h)).json()
    assert abs((card["item"]["remaining_qty"] or 0) - 88) < 1e-6

    blocked = await client.post(
        f"{OPS}/operations/{oid}/sale",
        json={"buyer_id": buyer["id"], "price": 10000, "ship": True, "allocations": [{"lot_id": lot_id, "quantity": 100}]},
        headers=h,
    )
    assert blocked.status == 400
    bjson = await blocked.json()
    assert "доступно" in (bjson.get("message_ru") or "").lower() or "нельзя" in (bjson.get("message_ru") or "").lower()
    assert abs(float(bjson.get("available") or 0) - 88) < 1e-6

    stock = await (await client.get(f"{OPS}/operations/stock", headers=h)).json()
    lot = next(x for x in stock["lots"] if x["id"] == lot_id)
    assert abs(lot["available"] - 88) < 1e-6

    assert card["pnl"].get("calculable") is True or card["pnl"].get("message_ru")
    assert card["cost_basis"].get("total_cost") is not None
    fifo = await (await client.post(f"{OPS}/operations/fifo-suggest", json={"crop": "Пшеница", "quantity": 50}, headers=h)).json()
    assert fifo["auto"] is False


async def test_rbac_and_tenant_isolation(client: TestClient):
    org_a = f"org-a22-a-{uuid.uuid4().hex[:8]}"
    org_b = f"org-a22-b-{uuid.uuid4().hex[:8]}"
    ha = _hdr(org_a)
    op = (await (await client.post(f"{OPS}/operations", json={"crop": "Ячмень", "planned_qty": 10}, headers=ha)).json())["item"]
    viewer = await client.post(f"{OPS}/operations", json={"crop": "Ячмень"}, headers=_hdr(org_a, "agro_viewer"))
    assert viewer.status == 403
    acc_exp = await client.post(f"{OPS}/operations/{op['id']}/expense", json={"amount": 1, "category": "lab"}, headers=_hdr(org_a, "agro_accountant"))
    assert acc_exp.status in {200, 201}
    logi = await client.post(f"{OPS}/operations/{op['id']}/expense", json={"amount": 1, "category": "transport"}, headers=_hdr(org_a, "agro_logistics"))
    assert logi.status == 403
    other = await client.get(f"{OPS}/operations/{op['id']}", headers=_hdr(org_b))
    assert other.status == 404
    listed = await (await client.get(f"{OPS}/operations", headers=_hdr(org_b))).json()
    assert listed["items"] == []


async def test_status_cannot_skip_and_search_finds_number(client: TestClient):
    org = f"org-a22-s-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    op = (await (await client.post(f"{OPS}/operations", json={"crop": "Кукуруза", "planned_qty": 1}, headers=h)).json()
          )["item"]
    bad = await client.post(f"{OPS}/operations/{op['id']}/status", json={"status": "sold"}, headers=h)
    assert bad.status == 400
    found = await (await client.get(f"{OPS}/search?q={op['number']}", headers=h)).json()
    ids = [i["id"] for g in found["groups"] for i in g["items"]]
    assert op["id"] in ids


async def test_transfer_no_double_count(client: TestClient):
    org = f"org-a22-t-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    a = (await (await client.post(f"{OPS}/entities/warehouse", json={"name": "A"}, headers=h)).json())["item"]
    b = (await (await client.post(f"{OPS}/entities/warehouse", json={"name": "B"}, headers=h)).json())["item"]
    op = (await (await client.post(f"{OPS}/operations", json={"crop": "Соя", "planned_qty": 20, "warehouse_id": a["id"]}, headers=h)).json())["item"]
    await client.post(f"{OPS}/operations/{op['id']}/weighing", json={"gross": 22, "tare": 2, "scale": "receiving", "unit": "т"}, headers=h)
    rec = await (await client.post(f"{OPS}/operations/{op['id']}/receive", json={}, headers=h)).json()
    lot_id = rec["item"]["id"]
    tr = await (
        await client.post(
            f"{OPS}/operations/{op['id']}/transfer",
            json={"lot_id": lot_id, "to_warehouse_id": b["id"], "quantity_sent": 10, "quantity_received": 9.5},
            headers=h,
        )
    ).json()
    assert tr["ok"] is True
    assert tr["item"]["difference"] == 0.5
    stock = await (await client.get(f"{OPS}/operations/stock", headers=h)).json()
    by_wh = {row["warehouse_id"]: row["quantity"] for row in stock["by_warehouse"]}
    assert abs(by_wh.get(a["id"], 0) - 10) < 1e-6
    assert abs(by_wh.get(b["id"], 0) - 9.5) < 1e-6
