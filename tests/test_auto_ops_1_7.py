"""Sprint AUTO 1.7 — logistics assignment, automation, audit, search, providers."""

from __future__ import annotations

import os
import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.auto_enterprise.api.register import register_auto_enterprise_routes
from services.auto_ops import reset_auto_ops_for_tests
from services.auto_ops.rbac import can, normalize_role

OPS = "/api/auto-ops/v1"
VIN = "1HGCM82633A004352"


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


def _hdr(org: str, role: str = "auto_director", principal: str | None = None, workspace: str | None = None) -> dict[str, str]:
    h = {"X-Organization-Id": org, "X-Role": role}
    if principal:
        h["X-Principal"] = principal
    if workspace:
        h["X-Workspace-Id"] = workspace
    return h


async def _vehicle(client: TestClient, org: str, vin: str = VIN, **body) -> str:
    payload = {"vin": vin, "manufacturer": "BMW", "model": "X5", "year": 2013, **body}
    res = await client.post(f"{OPS}/vehicles", json=payload, headers=_hdr(org))
    assert res.status == 201, await res.text()
    return (await res.json())["item"]["id"]


async def test_auto_ops_1_7_health_and_roles(client: TestClient):
    res = await client.get(f"{OPS}/health")
    body = await res.json()
    assert body["sprint"] in {"AUTO_1.7", "AUTO_1.8", "AUTO_1.8.5"}
    assert body["private"] is True
    assert "Новый бот не строится" in body["telegram"]["message_ru"]
    roles = await (await client.get(f"{OPS}/roles")).json()
    ids = {r["id"] for r in roles["roles"]}
    assert {"auto_director", "auto_accountant", "auto_manager", "auto_admin"} <= ids
    assert "auto_forwarder" in ids
    assert "auto_customs" in ids
    assert normalize_role("экспедитор") == "auto_forwarder"
    assert normalize_role("таможня") == "auto_customs"
    assert can("auto_forwarder", "edit")
    assert not can("auto_forwarder", "finance")
    assert can("auto_customs", "edit")
    assert not can("auto_customs", "finance")
    assert not can("auto_accountant", "edit")
    assert not can("auto_manager", "finance")
    catalogs = (await (await client.get(f"{OPS}/catalogs", headers=_hdr("auto-a17-x"))).json())["catalogs"]
    assert catalogs["tracking_policy"]["live_ais"] is False
    assert any(s["id"] == "MANUAL" for s in catalogs["event_sources"])


async def test_manager_assignment_policy_and_suggested_tasks(client: TestClient):
    org = f"auto-a17-{uuid.uuid4().hex[:8]}"
    vid = await _vehicle(client, org)
    h = _hdr(org)
    created = await client.post(f"{OPS}/logistics/shipments", json={"vehicle_id": vid, "shipment_type": "CONTAINER"}, headers=h)
    assert created.status == 201, await created.text()
    first = await created.json()
    sid = first["item"]["id"]
    assert first["item"]["shipment_number"].startswith("SHP-")

    await client.post(
        f"{OPS}/logistics/settings",
        json={"require_manager_on_active_shipment": True},
        headers=_hdr(org, "auto_admin"),
    )
    blocked = await client.post(
        f"{OPS}/logistics/shipments",
        json={"vehicle_id": vid, "shipment_type": "CONTAINER", "status": "BOOKED"},
        headers=h,
    )
    assert blocked.status == 400
    assert (await blocked.json())["field"] == "responsible_manager_id"

    ok = await client.post(
        f"{OPS}/logistics/shipments",
        json={"vehicle_id": vid, "shipment_type": "CONTAINER", "status": "PLANNED", "responsible_manager_id": "mgr-17"},
        headers=h,
    )
    assert ok.status == 201
    sid2 = (await ok.json())["item"]["id"]
    booked = await client.post(f"{OPS}/logistics/shipments/{sid2}", json={"status": "BOOKED"}, headers=h)
    assert booked.status == 200, await booked.text()
    body = await booked.json()
    titles = {t["title"] for t in body.get("suggested_tasks") or []}
    assert "Получить Bill of Lading" in titles
    tasks = await (await client.get(f"{OPS}/tasks?shipment_id={sid2}", headers=h)).json()
    assert any(t.get("title") == "Получить Bill of Lading" and t.get("suggested") for t in tasks["items"])

    await client.post(f"{OPS}/logistics/shipments/{sid}", json={"responsible_manager_id": "mgr-17"}, headers=h)
    port = await client.post(f"{OPS}/logistics/shipments/{sid}", json={"status": "ARRIVED_DESTINATION_PORT"}, headers=h)
    assert any(t["title"] == "Подготовить таможню" for t in (await port.json()).get("suggested_tasks") or [])
    handoff = await client.post(f"{OPS}/logistics/shipments/{sid}", json={"status": "CUSTOMS_HANDOFF"}, headers=h)
    assert any(t["title"] == "Назначить автовоз" for t in (await handoff.json()).get("suggested_tasks") or [])


async def test_audit_event_source_confirmation_and_search(client: TestClient):
    org = f"auto-a17-{uuid.uuid4().hex[:8]}"
    vid = await _vehicle(client, org, assigned_manager_id="mgr-17")
    h = _hdr(org)
    client_res = await client.post(f"{OPS}/clients", json={"name": "GlobeFly LLC", "phone": "+380501110011"}, headers=h)
    cid = (await client_res.json())["item"]["id"]
    await client.post(f"{OPS}/vehicles/{vid}", json={"client_id": cid}, headers=h)
    ship = await client.post(
        f"{OPS}/logistics/shipments",
        json={
            "vehicle_id": vid,
            "shipment_type": "CONTAINER",
            "booking_number": "BKG-17",
            "bill_of_lading_number": "BL-17-AAA",
            "responsible_manager_id": "mgr-17",
            "assigned_forwarder_id": "fwd-1",
            "accountant_reviewer_id": "acc-1",
            "customs_responsible_id": "cst-1",
        },
        headers=h,
    )
    sid = (await ship.json())["item"]["id"]
    number = (await ship.json())["item"]["shipment_number"]
    ctr = await client.post(f"{OPS}/logistics/containers", json={"container_number": "MSCU1234567", "container_type": "40HC"}, headers=h)
    container_id = (await ctr.json())["item"]["id"]
    await client.post(f"{OPS}/logistics/shipments/{sid}", json={"container_id": container_id}, headers=h)
    await client.post(f"{OPS}/logistics/shipments/{sid}", json={"current_eta": "2026-09-12"}, headers=h)
    ev = await client.post(
        f"{OPS}/logistics/shipments/{sid}/events",
        json={"event_type": "comment", "description": "На складе", "location": "Savannah", "source": "manual"},
        headers=h,
    )
    assert ev.status in {200, 201}, await ev.text()
    event = (await ev.json())["item"]
    assert event["source"] == "MANUAL"
    assert event["confirmation"] == "CONFIRMED"
    weak = await client.post(
        f"{OPS}/logistics/shipments/{sid}/events",
        json={"event_type": "comment", "description": "импорт CSV", "source": "import"},
        headers=h,
    )
    assert (await weak.json())["item"]["confirmation"] == "UNCONFIRMED"
    await client.post(f"{OPS}/expenses", json={"vehicle_id": vid, "shipment_id": sid, "category": "SEA_FREIGHT", "amount": 900}, headers=h)
    await client.post(
        f"{OPS}/documents",
        json={"owner_type": "shipment", "shipment_id": sid, "vehicle_id": vid, "file_name": "bl.pdf", "document_type": "bill_of_lading"},
        headers=h,
    )

    listed = await (await client.get(f"{OPS}/logistics/shipments?q=BL-17-AAA", headers=h)).json()
    assert listed["total"] >= 1
    by_client = await (await client.get(f"{OPS}/logistics/shipments?q=GlobeFly", headers=h)).json()
    assert by_client["total"] >= 1
    by_num = await (await client.get(f"{OPS}/logistics/shipments?q={number}", headers=h)).json()
    assert by_num["total"] >= 1

    search = await (await client.get(f"{OPS}/search?q=BL-17-AAA", headers=h)).json()
    kinds = {i["kind"] for i in search["items"]}
    assert "bol" in kinds
    assert "shipment" in kinds
    vin_hits = await (await client.get(f"{OPS}/search?q={VIN}", headers=h)).json()
    assert {i["kind"] for i in vin_hits["items"]} & {"vehicle", "shipment"}
    client_hits = await (await client.get(f"{OPS}/search?q=GlobeFly", headers=h)).json()
    assert any(i["kind"] == "client" for i in client_hits["items"])
    ctr_hits = await (await client.get(f"{OPS}/search?q=MSCU1234567", headers=h)).json()
    assert any(i["kind"] == "container" for i in ctr_hits["items"])

    audit = await (await client.get(f"{OPS}/audit", headers=h)).json()
    actions = {a["action"] for a in audit["items"]}
    assert "shipment_created" in actions
    assert "vehicle_linked" in actions
    assert "container_assigned" in actions
    assert "eta_changed" in actions
    assert "event_added" in actions
    assert "expense_allocated" in actions
    assert "document_linked" in actions
    assert "location_updated" in actions

    hist = await (await client.get(f"{OPS}/logistics/vehicles/{vid}/history", headers=h)).json()
    assert hist["total"] >= 1
    assert hist["items"] == sorted(hist["items"], key=lambda r: str(r.get("at") or ""))


async def test_tenant_isolation_rbac_and_manager_cost(client: TestClient):
    org_a = f"auto-a17-{uuid.uuid4().hex[:8]}"
    org_b = f"auto-a17-{uuid.uuid4().hex[:8]}"
    vid_a = await _vehicle(client, org_a)
    vid_b = await _vehicle(client, org_b, vin="WBAFR9C50DD123456")
    sa = await client.post(
        f"{OPS}/logistics/shipments",
        json={"vehicle_id": vid_a, "shipment_type": "UA_TRUCK", "workspace_id": "ws-a", "responsible_manager_id": "mgr-a"},
        headers=_hdr(org_a),
    )
    assert sa.status == 201
    await client.post(
        f"{OPS}/logistics/shipments",
        json={"vehicle_id": vid_b, "shipment_type": "UA_TRUCK", "workspace_id": "ws-b"},
        headers=_hdr(org_b),
    )
    listed_a = await (await client.get(f"{OPS}/logistics/shipments?workspace_id=ws-a", headers=_hdr(org_a))).json()
    assert listed_a["total"] == 1
    assert all(i.get("workspace_id") == "ws-a" for i in listed_a["items"])
    other_ws = await (await client.get(f"{OPS}/logistics/shipments?workspace_id=ws-b", headers=_hdr(org_a))).json()
    assert other_ws["total"] == 0
    cross = await (await client.get(f"{OPS}/logistics/shipments", headers=_hdr(org_b))).json()
    assert all(i.get("organization_id") == org_b for i in cross["items"])

    sid = (await sa.json())["item"]["id"]
    await client.post(f"{OPS}/expenses", json={"vehicle_id": vid_a, "shipment_id": sid, "category": "UA_TRANSPORT", "amount": 300}, headers=_hdr(org_a))
    mgr = await (await client.get(f"{OPS}/logistics/shipments/{sid}", headers=_hdr(org_a, "auto_manager", principal="mgr-a"))).json()
    costs = mgr["item"]["costs"]
    assert costs.get("restricted") is not True
    assert costs.get("operational_only") is True
    assert costs.get("profit") is None
    assert costs["actual"] == 300 or costs["planned"] == 300

    acc_status = await client.post(
        f"{OPS}/logistics/shipments/{sid}",
        json={"status": "IN_TRANSIT"},
        headers=_hdr(org_a, "auto_accountant"),
    )
    assert acc_status.status == 403

    admin_create = await client.post(
        f"{OPS}/logistics/shipments",
        json={"vehicle_id": vid_a, "shipment_type": "OTHER"},
        headers=_hdr(org_a, "auto_admin"),
    )
    assert admin_create.status == 403

    fwd = await client.post(
        f"{OPS}/logistics/shipments/{sid}/events",
        json={"event_type": "comment", "description": "экспедитор"},
        headers=_hdr(org_a, "auto_forwarder", principal="fwd-1"),
    )
    assert fwd.status in {200, 201}, await fwd.text()


async def test_providers_never_expose_secrets_and_fallback(client: TestClient, monkeypatch):
    org = f"auto-a17-{uuid.uuid4().hex[:8]}"
    vid = await _vehicle(client, org)
    ship = await client.post(
        f"{OPS}/logistics/shipments",
        json={"vehicle_id": vid, "shipment_type": "SEA_FREIGHT", "tracking_url": "https://line.example/track/1"},
        headers=_hdr(org),
    )
    sid = (await ship.json())["item"]["id"]
    created = await client.post(
        f"{OPS}/logistics/providers",
        json={"name": "Demo Line", "type": "ais", "url": "https://line.example", "api_key_env": "AUTO_TRACKING_KEY", "enabled": True, "api_key": "super-secret"},
        headers=_hdr(org, "auto_admin"),
    )
    assert created.status in {200, 201}, await created.text()
    item = (await created.json())["item"]
    assert "super-secret" not in str(item)
    assert item.get("api_key") is None
    assert item["api_key_env"] == "AUTO_TRACKING_KEY"
    monkeypatch.delenv("AUTO_TRACKING_KEY", raising=False)
    check = await client.post(f"{OPS}/logistics/providers/{item['id']}/check", headers=_hdr(org))
    body = await check.json()
    assert body["available"] is False
    assert "Автоматическое отслеживание недоступно" in (body.get("message_ru") or "")
    track = await (await client.get(f"{OPS}/logistics/shipments/{sid}/tracking", headers=_hdr(org))).json()
    assert track["available"] is False
    assert track["manual_event_allowed"] is True
    assert track["source_url"] == "https://line.example/track/1"
    os.environ["AUTO_TRACKING_KEY"] = "present-not-returned"
    try:
        ready = await client.post(f"{OPS}/logistics/providers/{item['id']}/check", headers=_hdr(org))
        ready_body = await ready.json()
        assert ready_body["available"] is True
        listed = await (await client.get(f"{OPS}/logistics/providers", headers=_hdr(org))).json()
        blob = str(listed)
        assert "present-not-returned" not in blob
        assert "super-secret" not in blob
    finally:
        os.environ.pop("AUTO_TRACKING_KEY", None)


async def test_director_logistics_averages_from_records(client: TestClient):
    org = f"auto-a17-{uuid.uuid4().hex[:8]}"
    vid = await _vehicle(client, org)
    await client.post(
        f"{OPS}/logistics/shipments",
        json={
            "vehicle_id": vid,
            "shipment_type": "CONTAINER",
            "etd": "2026-08-01",
            "eta": "2026-08-21",
            "ata": "2026-08-10",
            "atd": "2026-08-12",
            "customs_handoff_date": "2026-08-13",
            "delivery_date_actual": "2026-08-16",
            "planned_eta": "2026-08-18",
            "current_eta": "2026-08-21",
        },
        headers=_hdr(org),
    )
    metrics = (await (await client.get(f"{OPS}/analytics/logistics", headers=_hdr(org))).json())["metrics"]
    assert metrics["avg_transit_days"] is not None
    assert metrics["avg_port_days"] == 2.0
    assert metrics["avg_customs_days"] == 3.0
    assert metrics["avg_delay_days"] == 3.0
    mgr = await (await client.get(f"{OPS}/analytics/logistics", headers=_hdr(org, "auto_manager", principal="mgr-x"))).json()
    assert mgr["metrics"]["avg_logistics_cost"] is None
    assert mgr.get("finance_restricted") is True
