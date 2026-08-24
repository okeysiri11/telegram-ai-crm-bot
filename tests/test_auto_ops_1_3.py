"""Sprint AUTO 1.3 — CRM / sales / payments / reports / privacy / audit."""

from __future__ import annotations

import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.auto_enterprise.api.register import register_auto_enterprise_routes
from services.auto_ops import reset_auto_ops_for_tests
from services.auto_ops.crm_catalog import profit_snapshot
from services.auto_ops.rbac import can

OPS = "/api/auto-ops/v1"
VIN = "1HGCM82633A004352"
DEMO_VIN = "WBAFR9C50DD777777"


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


def _hdr(org: str, role: str = "auto_manager") -> dict[str, str]:
    return {"X-Organization-Id": org, "X-Role": role}


async def _vehicle(client: TestClient, org: str, vin: str = VIN, role: str = "auto_manager") -> str:
    res = await client.post(
        f"{OPS}/vehicles",
        json={"vin": vin, "manufacturer": "BMW", "model": "X5", "year": 2013, "auction_url": "https://a"},
        headers=_hdr(org, role),
    )
    assert res.status == 201, await res.text()
    return (await res.json())["item"]["id"]


async def _client_row(client: TestClient, org: str, name: str = "Иванов", role: str = "auto_manager", **extra) -> str:
    res = await client.post(f"{OPS}/clients", json={"name": name, **extra}, headers=_hdr(org, role))
    assert res.status == 201, await res.text()
    return (await res.json())["item"]["id"]


async def test_health_is_auto_1_3(client: TestClient):
    res = await client.get(f"{OPS}/health")
    body = await res.json()
    assert body["sprint"] in {"AUTO_1.3", "AUTO_1.4", "AUTO_1.5", "AUTO_1.6", "AUTO_1.7", "AUTO_1.8", "AUTO_1.8.5"}
    assert body["telegram"]["status"] in {"prepared", "live"}
    intents = {i["command"] for i in body["telegram"]["intents"]}
    assert "/client <name>" in intents
    assert "/deal <VIN>" in intents
    assert "/sale <VIN>" in intents
    assert "/logistics <VIN>" in intents
    assert "Новый бот не строится" in body["telegram"]["message_ru"]


def test_profit_snapshot_never_invents():
    empty = profit_snapshot(cost=0, revenue=0)
    assert empty["incomplete"] is True
    assert empty["roi_pct"] is None
    assert empty["margin_pct"] is None
    snap = profit_snapshot(cost=18000, revenue=28000)
    assert snap["profit"] == 10000
    assert snap["roi_pct"] == 55.56
    assert snap["margin_pct"] == 35.71
    assert snap["from_records"] is True


async def test_client_crud_pii_redaction(client: TestClient):
    org = f"auto-c13-{uuid.uuid4().hex[:8]}"
    director = _hdr(org, "auto_director")
    manager = _hdr(org)
    accountant = _hdr(org, "auto_accountant")
    created = await client.post(
        f"{OPS}/clients",
        json={"name": "Петров", "phone": "+380501112233", "email": "p@example.com", "address": "Kyiv, Demo 1", "passport_ref": "AB123"},
        headers=director,
    )
    assert created.status == 201
    cid = (await created.json())["item"]["id"]
    assert (await created.json())["item"]["address"] == "Kyiv, Demo 1"

    mgr_view = await client.get(f"{OPS}/clients/{cid}", headers=manager)
    assert mgr_view.status == 200
    mitem = (await mgr_view.json())["item"]
    assert mitem["phone"] == "+380501112233"
    assert mitem["address"] == "***"
    assert mitem["passport_ref"] == "***"

    acc_list = await client.get(f"{OPS}/clients", headers=accountant)
    assert acc_list.status == 200
    acc_row = next(x for x in (await acc_list.json())["items"] if x["id"] == cid)
    assert acc_row["phone"] == "***"
    assert acc_row["email"] == "***"

    forbidden_pii = await client.post(f"{OPS}/clients/{cid}", json={"address": "new"}, headers=manager)
    assert forbidden_pii.status == 403

    renamed = await client.post(f"{OPS}/clients/{cid}", json={"name": "Петров А."}, headers=manager)
    assert renamed.status == 200
    assert (await renamed.json())["item"]["name"] == "Петров А."


async def test_lead_pipeline_stage_persistence(client: TestClient):
    org = f"auto-pipe-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    cid = await _client_row(client, org)
    vid = await _vehicle(client, org)
    created = await client.post(f"{OPS}/crm/deals", json={"client_id": cid, "vehicle_id": vid, "stage": "LEAD", "assigned_manager_id": "mgr-1"}, headers=h)
    assert created.status == 201, await created.text()
    deal = (await created.json())["item"]
    did = deal["id"]
    assert deal["stage"] == "LEAD"
    assert deal["answers"]["client"]
    assert deal["answers"]["stage"] == "Лид"

    bad = await client.post(f"{OPS}/crm/deals/{did}", json={"stage": "flying"}, headers=h)
    assert bad.status == 400

    ok = await client.post(f"{OPS}/crm/deals/{did}", json={"stage": "CONTACT"}, headers=h)
    assert ok.status == 200
    body = await ok.json()
    assert body["item"]["stage"] == "CONTACT"
    steps = {s["id"]: s["state"] for s in body["item"]["pipeline"]}
    assert steps["contact"] == "current"

    listed = await client.get(f"{OPS}/crm/deals?tab=leads", headers=h)
    assert listed.status == 200
    assert any(x["id"] == did for x in (await listed.json())["items"])

    got = await client.get(f"{OPS}/crm/deals/{did}", headers=h)
    assert (await got.json())["item"]["stage"] == "CONTACT"


async def test_reservation_conflict_expiry_override(client: TestClient):
    org = f"auto-rsv-{uuid.uuid4().hex[:8]}"
    mgr = _hdr(org)
    director = _hdr(org, "auto_director")
    vid = await _vehicle(client, org)
    c1 = await _client_row(client, org, "Первый")
    c2 = await _client_row(client, org, "Второй")
    first = await client.post(f"{OPS}/crm/reservations", json={"vehicle_id": vid, "client_id": c1, "expires_at": "2020-01-01"}, headers=mgr)
    assert first.status == 201, await first.text()
    rid = (await first.json())["item"]["id"]

    listed = await client.get(f"{OPS}/crm/reservations?vehicle_id={vid}", headers=mgr)
    item = next(x for x in (await listed.json())["items"] if x["id"] == rid)
    assert item["status"] == "EXPIRED"

    active = await client.post(f"{OPS}/crm/reservations", json={"vehicle_id": vid, "client_id": c1, "expires_at": "2026-12-31"}, headers=mgr)
    assert active.status == 201
    conflict = await client.post(f"{OPS}/crm/reservations", json={"vehicle_id": vid, "client_id": c2}, headers=mgr)
    assert conflict.status == 409

    override = await client.post(
        f"{OPS}/crm/reservations",
        json={"vehicle_id": vid, "client_id": c2, "override": True, "override_reason": "director"},
        headers=director,
    )
    assert override.status == 201, await override.text()

    cancel = await client.post(f"{OPS}/crm/reservations/{(await override.json())['item']['id']}", json={"status": "CANCELLED"}, headers=mgr)
    assert cancel.status == 200
    assert (await cancel.json())["item"]["status"] == "CANCELLED"


async def test_sale_sold_conflict_and_vehicle_status(client: TestClient):
    org = f"auto-sale-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    vid = await _vehicle(client, org)
    cid = await _client_row(client, org)
    deal = await client.post(f"{OPS}/crm/deals", json={"client_id": cid, "vehicle_id": vid, "sale_price": 25000}, headers=h)
    did = (await deal.json())["item"]["id"]
    sale = await client.post(f"{OPS}/crm/sales", json={"vehicle_id": vid, "client_id": cid, "deal_id": did, "price": 25000, "status": "OPEN"}, headers=h)
    assert sale.status == 201, await sale.text()
    sid = (await sale.json())["item"]["id"]
    done = await client.post(f"{OPS}/crm/sales/{sid}", json={"status": "COMPLETED"}, headers=h)
    assert done.status == 200
    profile = await client.get(f"{OPS}/vehicles/{vid}", headers=h)
    body = await profile.json()
    assert body["item"]["status"] == "SOLD"
    assert body["crm"]["deal"]["stage"] == "COMPLETED"
    second = await client.post(f"{OPS}/crm/sales", json={"vehicle_id": vid, "client_id": cid, "price": 1}, headers=h)
    assert second.status == 409
    reserve = await client.post(f"{OPS}/crm/reservations", json={"vehicle_id": vid, "client_id": cid}, headers=h)
    assert reserve.status == 409
    hard = await client.post(f"{OPS}/crm/sales/{sid}", json={"delete": True}, headers=h)
    assert hard.status == 409


async def test_partial_payments_aggregation_outstanding_refund(client: TestClient):
    org = f"auto-pay-{uuid.uuid4().hex[:8]}"
    mgr = _hdr(org)
    acc = _hdr(org, "auto_accountant")
    vid = await _vehicle(client, org)
    cid = await _client_row(client, org)
    deal = await client.post(f"{OPS}/crm/deals", json={"client_id": cid, "vehicle_id": vid, "sale_price": 28000, "currency": "USD"}, headers=mgr)
    did = (await deal.json())["item"]["id"]

    pending = await client.post(
        f"{OPS}/crm/receipts",
        json={"deal_id": did, "kind": "DEPOSIT", "amount": 5000, "currency": "USD", "status": "pending", "reference": "PAY-DEP"},
        headers=mgr,
    )
    assert pending.status == 201
    rid = (await pending.json())["item"]["id"]
    confirm_forbidden = await client.post(f"{OPS}/crm/receipts/{rid}", json={"status": "confirmed"}, headers=mgr)
    assert confirm_forbidden.status == 403
    confirmed = await client.post(f"{OPS}/crm/receipts/{rid}", json={"status": "confirmed"}, headers=acc)
    assert confirmed.status == 200

    await client.post(f"{OPS}/crm/receipts", json={"deal_id": did, "kind": "PARTIAL", "amount": 10000, "status": "confirmed"}, headers=acc)
    got = await client.get(f"{OPS}/crm/deals/{did}", headers=mgr)
    pay = (await got.json())["item"]["payments"]
    assert pay["paid"] == 15000
    assert pay["outstanding"] == 13000
    assert pay["from_records"] is True

    hard = await client.post(f"{OPS}/crm/receipts/{rid}", json={"delete": True}, headers=acc)
    assert hard.status == 409
    edit_amt = await client.post(f"{OPS}/crm/receipts/{rid}", json={"amount": 1}, headers=acc)
    assert edit_amt.status == 409

    refunded = await client.post(f"{OPS}/crm/receipts/{rid}", json={"refund": True}, headers=acc)
    assert refunded.status == 200
    assert (await refunded.json())["item"]["status"] == "refunded"
    after = (await (await client.get(f"{OPS}/crm/deals/{did}", headers=mgr)).json())["item"]["payments"]
    assert after["paid"] == 10000
    assert after["outstanding"] == 18000


async def test_profit_roi_margin_from_records(client: TestClient):
    org = f"auto-profit-{uuid.uuid4().hex[:8]}"
    mgr = _hdr(org)
    acc = _hdr(org, "auto_accountant")
    vid = await _vehicle(client, org)
    cid = await _client_row(client, org)
    deal = await client.post(f"{OPS}/crm/deals", json={"client_id": cid, "vehicle_id": vid, "sale_price": 28000}, headers=mgr)
    did = (await deal.json())["item"]["id"]
    exp = await client.post(f"{OPS}/expenses", json={"vehicle_id": vid, "category": "PURCHASE", "amount": 18000, "currency": "USD", "payment_status": "paid"}, headers=acc)
    assert exp.status == 201
    await client.post(f"{OPS}/crm/receipts", json={"deal_id": did, "kind": "FINAL", "amount": 28000, "status": "confirmed"}, headers=acc)
    got = await client.get(f"{OPS}/crm/deals/{did}", headers=acc)
    profit = (await got.json())["item"]["profit"]
    assert profit["cost"] == 18000
    assert profit["revenue"] == 28000
    assert profit["profit"] == 10000
    assert profit["roi_pct"] == 55.56
    assert profit["margin_pct"] == 35.71


async def test_document_permissions_rbac_audit_search_tasks(client: TestClient):
    org = f"auto-priv-{uuid.uuid4().hex[:8]}"
    director = _hdr(org, "auto_director")
    manager = _hdr(org)
    guest = _hdr(org, "client")
    admin = _hdr(org, "auto_admin")
    vid = await _vehicle(client, org, role="auto_director")
    cid = await _client_row(client, org, "Секрет", role="auto_director", phone="+380679990011")
    deal = await client.post(f"{OPS}/crm/deals", json={"client_id": cid, "vehicle_id": vid, "stage": "LEAD", "assigned_manager_id": "mgr-a"}, headers=director)
    did = (await deal.json())["item"]["id"]

    guest_ops = await client.get(f"{OPS}/crm/deals", headers=guest)
    assert guest_ops.status == 403
    admin_create = await client.post(f"{OPS}/crm/deals", json={"client_id": cid}, headers=admin)
    assert admin_create.status == 403

    doc = await client.post(
        f"{OPS}/documents",
        json={"owner_type": "client", "client_id": cid, "deal_id": did, "file_name": "passport.pdf", "document_type": "passport"},
        headers=director,
    )
    assert doc.status == 201
    doc_id = (await doc.json())["item"]["id"]
    mgr_doc = await client.get(f"{OPS}/documents/{doc_id}", headers=manager)
    assert mgr_doc.status == 403
    dir_doc = await client.get(f"{OPS}/documents/{doc_id}", headers=director)
    assert dir_doc.status == 200

    reassign = await client.post(f"{OPS}/clients/{cid}", json={"assigned_manager_id": "mgr-b"}, headers=director)
    assert reassign.status == 200
    task = await client.post(f"{OPS}/tasks", json={"title": "Позвонить клиенту", "vehicle_id": vid, "client_id": cid, "deal_id": did, "assigned_manager_id": "mgr-b"}, headers=manager)
    assert task.status == 201
    assert (await task.json())["item"]["deal_id"] == did

    notes = await client.get(f"{OPS}/logistics/notifications", headers=director)
    assert notes.status == 200
    titles = {n.get("notification_type") for n in (await notes.json())["items"]}
    assert "deal_created" in titles

    search = await client.get(f"{OPS}/search?q={VIN}", headers=manager)
    kinds = {h["kind"] for h in (await search.json())["items"]}
    assert "vehicle" in kinds
    phone = await client.get(f"{OPS}/search?q=380679990011", headers=manager)
    assert any(h["kind"] == "client" for h in (await phone.json())["items"])
    docs = await client.get(f"{OPS}/search?q=passport.pdf", headers=manager)
    assert any(h["kind"] == "document" for h in (await docs.json())["items"])

    audit = await client.get(f"{OPS}/audit", headers=director)
    actions = {a["action"] for a in (await audit.json())["items"]}
    assert "client_created" in actions
    assert "lead_created" in actions
    assert "client_document_accessed" in actions
    assert "manager_reassigned" in actions


async def test_reports_manager_performance_no_scoring(client: TestClient):
    org = f"auto-rep-{uuid.uuid4().hex[:8]}"
    director = _hdr(org, "auto_director")
    manager = _hdr(org)
    vid = await _vehicle(client, org)
    cid = await _client_row(client, org)
    await client.post(f"{OPS}/crm/deals", json={"client_id": cid, "vehicle_id": vid, "assigned_manager_id": "mgr-1", "stage": "LEAD"}, headers=manager)
    funnel = await client.get(f"{OPS}/reports?report=funnel", headers=director)
    assert funnel.status == 200
    body = await funnel.json()
    labels = {row["label_ru"] for row in body["items"]}
    assert "Лид" in labels
    types = {t["id"] for t in body["types"]}
    assert {"sales", "vehicle_profit", "expenses", "receipts", "client_debt", "managers", "funnel", "in_stock", "in_transit"} <= types

    managers = await client.get(f"{OPS}/reports?report=managers", headers=director)
    mbody = await managers.json()
    assert mbody["employee_scoring"] is False
    row = mbody["items"][0]
    assert row["score"] is None
    assert row["ranking"] is None
    assert "leads_assigned" in row
    assert "contacts_made" in row
    assert "outstanding_tasks" in row

    mgr_denied = await client.get(f"{OPS}/reports?report=sales", headers=manager)
    assert mgr_denied.status == 403
    assert not can("auto_manager", "reports")


async def test_soft_delete_expense_and_demo_scenario(client: TestClient):
    org = f"auto-demo-{uuid.uuid4().hex[:8]}"
    director = _hdr(org, "auto_director")
    no_flag = await client.post(f"{OPS}/crm/demo", json={}, headers=director)
    assert no_flag.status == 400
    seeded = await client.post(f"{OPS}/crm/demo", json={"confirm_demo": True}, headers=director)
    assert seeded.status == 201, await seeded.text()
    body = await seeded.json()
    assert body["demo"] is True
    assert body["client"]["name"] == "DEMO CLIENT"
    assert body["vehicle"]["vin"] == DEMO_VIN
    deal = body["deal"]
    assert deal["is_demo"] is True
    assert deal["stage"] == "COMPLETED"
    assert deal["payments"]["paid"] == 28000
    assert deal["payments"]["outstanding"] == 0
    assert deal["profit"]["profit"] == 10000
    profile = await client.get(f"{OPS}/vehicles/{body['vehicle']['id']}", headers=director)
    pbody = await profile.json()
    assert pbody["item"]["status"] == "SOLD"
    assert pbody["logistics"] is not None
    assert pbody["customs"] is not None
    assert pbody["crm"]["deal"]["stage"] == "COMPLETED"

    search = await client.get(f"{OPS}/search?q=DEMO-DEP-1", headers=director)
    assert any(h["kind"] == "payment" for h in (await search.json())["items"])
    vin_hit = await client.get(f"{OPS}/search?q={DEMO_VIN}", headers=director)
    assert any(h["kind"] == "vehicle" for h in (await vin_hit.json())["items"])

    vid = body["vehicle"]["id"]
    exp = await client.post(f"{OPS}/expenses", json={"vehicle_id": vid, "category": "PURCHASE", "amount": 50, "payment_status": "paid"}, headers=director)
    eid = (await exp.json())["item"]["id"]
    deleted = await client.delete(f"{OPS}/expenses/{eid}", headers=director)
    assert deleted.status == 200
    dbody = await deleted.json()
    assert dbody.get("soft") is True
    assert dbody["item"]["payment_status"] == "cancelled"
    listed = await client.get(f"{OPS}/expenses?vehicle_id={vid}", headers=director)
    assert any(e["id"] == eid for e in (await listed.json())["items"])
