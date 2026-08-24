"""Sprint AUTO 1.1 — vehicle logistics / containers / ports / delay desk."""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.auto_enterprise.api.register import register_auto_enterprise_routes
from services.auto_ops import reset_auto_ops_for_tests
from services.auto_ops.logistics_catalog import delay_report
from services.auto_ops.rbac import can

OPS = "/api/auto-ops/v1"
VIN = "1HGCM82633A004352"
VIN2 = "1HGCM82633A004353"


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
        json={"vin": vin, "manufacturer": "BMW", "model": "X5", "auction_url": "https://a"},
        headers=_hdr(org, role),
    )
    assert res.status == 201, await res.text()
    return (await res.json())["item"]["id"]


async def test_health_is_auto_1_1(client: TestClient):
    res = await client.get(f"{OPS}/health")
    body = await res.json()
    assert body["sprint"] in {"AUTO_1.1", "AUTO_1.2", "AUTO_1.3", "AUTO_1.4", "AUTO_1.5", "AUTO_1.6", "AUTO_1.7", "AUTO_1.8", "AUTO_1.8.5"}
    assert body["telegram"]["status"] in {"prepared", "live"}
    intents = {i["command"] for i in body["telegram"]["intents"]}
    assert "/logistics <VIN>" in intents
    assert "/container <NUMBER>" in intents


async def test_delay_engine_from_stored_dates_only():
    green = delay_report(planned_eta="2026-08-20", current_eta="2026-08-20", status="SEA_TRANSIT", today=date(2026, 8, 10))
    assert green["level"] == "green"
    assert green["delay_days"] == 0
    yellow = delay_report(planned_eta="2026-08-20", current_eta="2026-08-22", status="SEA_TRANSIT", today=date(2026, 8, 10))
    assert yellow["level"] == "yellow"
    assert yellow["delay_days"] == 2
    orange = delay_report(planned_eta="2026-08-20", current_eta="2026-08-25", status="SEA_TRANSIT", today=date(2026, 8, 10), yellow_days=3, orange_days=7)
    assert orange["level"] == "orange"
    overdue = delay_report(planned_eta="2026-08-01", current_eta="2026-08-01", status="SEA_TRANSIT", today=date(2026, 8, 18))
    assert overdue["overdue"] is True
    assert overdue["level"] == "red"
    done = delay_report(planned_eta="2026-08-01", current_eta="2026-08-10", status="DELIVERED", today=date(2026, 8, 18))
    assert done["level"] == "green"
    assert done["eta_source_label_ru"] == "Введено вручную"


async def test_shipment_crud_vehicle_link_and_status(client: TestClient):
    org = f"auto-ship-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    vid = await _vehicle(client, org)
    created = await client.post(
        f"{OPS}/logistics/shipments",
        json={
            "vehicle_id": vid,
            "shipment_type": "CONTAINER",
            "origin_country": "US",
            "destination_country": "UA",
            "eta": "2026-08-25",
            "planned_eta": "2026-08-22",
        },
        headers=h,
    )
    assert created.status == 201, await created.text()
    ship = (await created.json())["item"]
    sid = ship["id"]
    assert ship["vehicle_id"] == vid
    assert ship["status"] == "PLANNED"
    assert ship["eta_source_label_ru"] == "Введено вручную"
    assert ship["tracking_mode"] == "manual"

    bad = await client.post(f"{OPS}/logistics/shipments/{sid}", json={"status": "flying"}, headers=h)
    assert bad.status == 400

    ok = await client.post(f"{OPS}/logistics/shipments/{sid}", json={"status": "SEA_TRANSIT"}, headers=h)
    assert ok.status == 200
    body = await ok.json()
    assert body["item"]["status"] == "SEA_TRANSIT"
    steps = {s["id"]: s["state"] for s in body["item"]["pipeline"]}
    assert steps["vessel"] == "current"

    listed = await client.get(f"{OPS}/logistics/shipments?tab=sea&q=BMW", headers=h)
    assert listed.status == 200
    assert any(x["id"] == sid for x in (await listed.json())["items"])

    profile = await client.get(f"{OPS}/vehicles/{vid}", headers=h)
    logistics = (await profile.json())["logistics"]
    assert logistics["shipment"]["id"] == sid
    assert logistics["shipment"]["status"] == "SEA_TRANSIT"


async def test_multi_vehicle_container_and_active_validation(client: TestClient):
    org = f"auto-ctr-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    v1 = await _vehicle(client, org, VIN)
    v2 = await _vehicle(client, org, VIN2)
    c1 = await client.post(f"{OPS}/logistics/containers", json={"container_number": "MSCU1234567", "container_type": "40HC"}, headers=h)
    assert c1.status == 201
    cid1 = (await c1.json())["item"]["id"]
    c2 = await client.post(f"{OPS}/logistics/containers", json={"container_number": "MSCU7654321", "container_type": "40FT"}, headers=h)
    cid2 = (await c2.json())["item"]["id"]

    a1 = await client.post(f"{OPS}/logistics/containers/{cid1}/vehicles", json={"vehicle_id": v1}, headers=h)
    a2 = await client.post(f"{OPS}/logistics/containers/{cid1}/vehicles", json={"vehicle_id": v2}, headers=h)
    assert a1.status == 201 and a2.status == 201

    conflict = await client.post(f"{OPS}/logistics/containers/{cid2}/vehicles", json={"vehicle_id": v1}, headers=h)
    assert conflict.status == 409

    reassign = await client.post(f"{OPS}/logistics/containers/{cid2}/vehicles", json={"vehicle_id": v1, "reassign": True}, headers=h)
    assert reassign.status == 201

    detail = await client.get(f"{OPS}/logistics/containers/{cid1}", headers=h)
    vehicles = (await detail.json())["vehicles"]
    active = [x for x in vehicles if not x.get("released_at")]
    assert any(str(x.get("vehicle_id")) == v2 for x in active)


async def test_carriers_drivers_trucks_vessels_ports(client: TestClient):
    org = f"auto-ref-{uuid.uuid4().hex[:8]}"
    mgr = _hdr(org, "auto_manager")
    director = _hdr(org, "auto_director")
    carrier = await client.post(f"{OPS}/logistics/carriers", json={"company_name": "Atlantic Trucking", "type": "truck", "country": "US"}, headers=mgr)
    assert carrier.status == 201
    driver = await client.post(
        f"{OPS}/logistics/drivers",
        json={"full_name": "John Doe", "passport_ref": "AB123", "driver_license": "DL-9", "carrier_id": (await carrier.json())["item"]["id"]},
        headers=mgr,
    )
    assert driver.status == 201
    listed = await client.get(f"{OPS}/logistics/drivers", headers=mgr)
    item = (await listed.json())["items"][0]
    assert item["passport_ref"] == "***"
    assert item["pii_restricted"] is True

    director_list = await client.get(f"{OPS}/logistics/drivers", headers=director)
    ditem = (await director_list.json())["items"][0]
    assert ditem["passport_ref"] == "AB123"

    truck = await client.post(f"{OPS}/logistics/trucks", json={"type": "car_transporter", "plate_number": "AA1234BB"}, headers=mgr)
    assert truck.status == 201
    vessel = await client.post(f"{OPS}/logistics/vessels", json={"name": "Atlantic Star", "eta": "2026-08-25"}, headers=mgr)
    assert vessel.status == 201
    vbody = await vessel.json()
    assert vbody["item"]["live_ais"] is False

    ports = await client.get(f"{OPS}/logistics/ports", headers=mgr)
    codes = {p.get("unlocode") for p in (await ports.json())["items"]}
    assert "USSAV" in codes and "UAODS" in codes

    fake = await client.post(f"{OPS}/logistics/ports", json={"name": "Fakeport", "unlocode": "XXFAK"}, headers=mgr)
    assert fake.status == 400


async def test_expenses_tasks_documents_notifications_audit(client: TestClient):
    org = f"auto-ops11-{uuid.uuid4().hex[:8]}"
    mgr = _hdr(org, "auto_manager")
    acc = _hdr(org, "auto_accountant")
    vid = await _vehicle(client, org)
    ship = await client.post(f"{OPS}/logistics/shipments", json={"vehicle_id": vid, "shipment_type": "SEA_FREIGHT", "eta": "2026-08-01"}, headers=mgr)
    sid = (await ship.json())["item"]["id"]

    still_forbidden = await client.post(f"{OPS}/expenses", json={"vehicle_id": vid, "category": "PURCHASE", "amount": 1000}, headers=mgr)
    assert still_forbidden.status == 403

    logistics_exp = await client.post(
        f"{OPS}/expenses",
        json={"vehicle_id": vid, "shipment_id": sid, "category": "SEA_FREIGHT", "amount": 1600, "payment_status": "planned"},
        headers=mgr,
    )
    assert logistics_exp.status == 201, await logistics_exp.text()

    await client.post(f"{OPS}/expenses", json={"vehicle_id": vid, "shipment_id": sid, "category": "PORT_FEE", "amount": 400, "payment_status": "paid"}, headers=acc)

    det = await client.get(f"{OPS}/logistics/shipments/{sid}", headers=acc)
    costs = (await det.json())["item"]["costs"]
    assert costs["planned"] == 1600
    assert costs["actual"] == 400
    assert costs["paid"] == 400

    prof = await client.get(f"{OPS}/vehicles/{vid}", headers=acc)
    finance = (await prof.json())["finance"]
    assert finance["cost"] == 2000

    task = await client.post(f"{OPS}/tasks", json={"title": "Получить B/L", "shipment_id": sid, "vehicle_id": vid, "priority": "high"}, headers=mgr)
    assert task.status == 201

    doc = await client.post(f"{OPS}/documents", json={"owner_type": "shipment", "shipment_id": sid, "vehicle_id": vid, "file_name": "bl.pdf", "document_type": "bill_of_lading"}, headers=mgr)
    assert doc.status == 201
    did = (await doc.json())["item"]["id"]
    deleted = await client.delete(f"{OPS}/documents/{did}", headers=_hdr(org, "auto_director"))
    assert deleted.status == 200
    assert (await deleted.json())["soft"] is True

    await client.post(f"{OPS}/logistics/shipments/{sid}", json={"status": "DELAYED", "current_eta": "2026-09-01"}, headers=mgr)
    notes = await client.get(f"{OPS}/logistics/notifications", headers=mgr)
    types = {n["notification_type"] for n in (await notes.json())["items"]}
    assert "shipment_delayed" in types or "eta_changed" in types

    audit = await client.get(f"{OPS}/audit", headers=_hdr(org, "auto_director"))
    actions = {a["action"] for a in (await audit.json())["items"]}
    assert "shipment_created" in actions
    assert "status_changed" in actions or "eta_changed" in actions


async def test_rbac_accountant_sees_logistics_admin_cannot_create(client: TestClient):
    org = f"auto-rbac11-{uuid.uuid4().hex[:8]}"
    vid = await _vehicle(client, org)
    mgr = _hdr(org)
    ship = await client.post(f"{OPS}/logistics/shipments", json={"vehicle_id": vid, "shipment_type": "UA_TRUCK"}, headers=mgr)
    assert ship.status == 201

    acc = await client.get(f"{OPS}/logistics/shipments", headers=_hdr(org, "auto_accountant"))
    assert acc.status == 200
    assert (await acc.json())["total"] == 1

    admin_create = await client.post(f"{OPS}/logistics/shipments", json={"vehicle_id": vid, "shipment_type": "OTHER"}, headers=_hdr(org, "auto_admin"))
    assert admin_create.status == 403

    guest = await client.get(f"{OPS}/logistics/shipments", headers=_hdr(org, "client"))
    assert guest.status == 403
    assert not can("auto_manager", "pii")
    assert can("auto_director", "pii")


async def test_demo_requires_confirm_and_is_labelled(client: TestClient):
    org = f"auto-demo-{uuid.uuid4().hex[:8]}"
    h = _hdr(org, "auto_director")
    denied = await client.post(f"{OPS}/logistics/demo", json={}, headers=h)
    assert denied.status == 400
    ok = await client.post(f"{OPS}/logistics/demo", json={"confirm_demo": True}, headers=h)
    assert ok.status == 201, await ok.text()
    body = await ok.json()
    assert body["demo"] is True
    assert body["vehicle"]["model"] == "X5"
    assert body["shipment"]["is_demo"] is True
    assert "Демо" in (body["label_ru"] or "")
