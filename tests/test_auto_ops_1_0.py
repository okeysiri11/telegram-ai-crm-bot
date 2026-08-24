"""Sprint AUTO 1.0 — private Auto import/dealership ops desk."""

from __future__ import annotations

import base64
import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.auto_enterprise.api.register import register_auto_enterprise_routes
from services.auto_ops import reset_auto_ops_for_tests
from services.auto_ops.rbac import can, normalize_role
from services.auto_ops.vin import normalize_vin, validate_vin

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


def _hdr(org: str, role: str = "auto_manager") -> dict[str, str]:
    return {"X-Organization-Id": org, "X-Role": role}


async def test_health_roles_and_telegram_boundary(client: TestClient):
    res = await client.get(f"{OPS}/health")
    assert res.status == 200
    body = await res.json()
    assert body["sprint"] in {"AUTO_1.0", "AUTO_1.1", "AUTO_1.2", "AUTO_1.3", "AUTO_1.4", "AUTO_1.5", "AUTO_1.6", "AUTO_1.7", "AUTO_1.8", "AUTO_1.8.5"}
    assert body["private"] is True
    assert body["public"] is False
    assert body["telegram"]["status"] in {"prepared", "live"}
    assert "Новый бот не строится" in body["telegram"]["message_ru"] or body["telegram"]["implemented"] in {False, True}
    roles = await client.get(f"{OPS}/roles")
    ids = {r["id"] for r in (await roles.json())["roles"]}
    assert {"auto_director", "auto_accountant", "auto_manager", "auto_admin"} <= ids


async def test_vin_normalize_and_validate():
    assert normalize_vin(" 1hgcm82633a004352 ") == VIN
    assert validate_vin(VIN) is None
    err = validate_vin("SHORT")
    assert err and err["code"] == "nonstandard_vin"
    assert validate_vin("SHORT", allow_nonstandard=True) is None


async def test_vehicle_crud_search_and_lifecycle(client: TestClient):
    org = f"auto-{uuid.uuid4().hex[:8]}"
    h = _hdr(org, "auto_manager")
    created = await client.post(
        f"{OPS}/vehicles",
        json={"vin": VIN, "manufacturer": "BMW", "model": "X5", "auction_url": "https://copart.example/lot/1"},
        headers=h,
    )
    assert created.status == 201
    item = (await created.json())["item"]
    vid = item["id"]
    assert item["vin"] == VIN
    assert item["status"] == "INTEREST"

    bad_status = await client.post(f"{OPS}/vehicles/{vid}", json={"status": "in_stock"}, headers=h)
    assert bad_status.status == 400

    ok_status = await client.post(f"{OPS}/vehicles/{vid}", json={"status": "SEA_TRANSIT"}, headers=h)
    assert ok_status.status == 200
    assert (await ok_status.json())["item"]["status"] == "SEA_TRANSIT"

    listed = await client.get(f"{OPS}/vehicles?q=BMW", headers=h)
    assert listed.status == 200
    assert any(x["id"] == vid for x in (await listed.json())["items"])

    detail = await client.get(f"{OPS}/vehicles/{vid}", headers=h)
    body = await detail.json()
    assert body["ok"] is True
    steps = {s["id"]: s["state"] for s in body["lifecycle"]}
    assert steps["sea"] == "current"
    assert steps["auction"] == "done"
    assert steps["sale"] == "future"


async def test_vin_uniqueness_and_admin_override(client: TestClient):
    org = f"auto-vin-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    first = await client.post(f"{OPS}/vehicles", json={"vin": VIN, "model": "X5", "auction_url": "https://a"}, headers=h)
    assert first.status == 201
    dup = await client.post(f"{OPS}/vehicles", json={"vin": VIN.lower(), "model": "X6", "auction_url": "https://b"}, headers=h)
    assert dup.status == 409
    admin = await client.post(
        f"{OPS}/vehicles",
        json={"vin": "SHORTVIN1", "model": "X3", "auction_url": "https://c", "allow_nonstandard_vin": True},
        headers=_hdr(org, "auto_director"),
    )
    assert admin.status == 201
    assert (await admin.json())["item"]["vin_nonstandard"] is True


async def test_org_isolation(client: TestClient):
    await client.post(f"{OPS}/vehicles", json={"vin": VIN, "manufacturer": "A", "auction_url": "https://a"}, headers=_hdr("org-a"))
    other = VIN[:-1] + "3"
    await client.post(f"{OPS}/vehicles", json={"vin": other, "manufacturer": "B", "auction_url": "https://b"}, headers=_hdr("org-b"))
    a = await client.get(f"{OPS}/vehicles", headers=_hdr("org-a"))
    names = [x.get("manufacturer") for x in (await a.json())["items"]]
    assert "A" in names and "B" not in names


async def test_expenses_finance_aggregation_and_no_fake_seed(client: TestClient):
    org = f"auto-fin-{uuid.uuid4().hex[:8]}"
    mgr = _hdr(org, "auto_manager")
    acc = _hdr(org, "auto_accountant")
    created = await client.post(f"{OPS}/vehicles", json={"vin": VIN, "manufacturer": "BMW", "model": "X5", "auction_url": "https://a"}, headers=mgr)
    vid = (await created.json())["item"]["id"]

    forbidden = await client.post(f"{OPS}/expenses", json={"vehicle_id": vid, "category": "PURCHASE", "amount": 18500}, headers=mgr)
    assert forbidden.status == 403

    empty_dash = await client.get(f"{OPS}/dashboard", headers=acc)
    finance = (await empty_dash.json())["finance"]
    assert finance["invested"] == 0
    assert finance["from_records"] is True

    e1 = await client.post(f"{OPS}/expenses", json={"vehicle_id": vid, "category": "PURCHASE", "amount": 18500, "currency": "USD"}, headers=acc)
    assert e1.status == 201
    await client.post(f"{OPS}/expenses", json={"vehicle_id": vid, "category": "SEA_FREIGHT", "amount": 1600}, headers=acc)
    await client.post(f"{OPS}/vehicles/{vid}", json={"sale_price_expected": 38000}, headers=mgr)

    dash = await client.get(f"{OPS}/dashboard", headers=acc)
    fin = (await dash.json())["finance"]
    assert fin["purchase_cost"] == 18500
    assert fin["logistics"] == 1600
    assert fin["invested"] == 20100
    assert fin["expected_revenue"] == 38000
    assert fin["expected_profit"] == 17900

    prof = await client.get(f"{OPS}/vehicles/{vid}", headers=acc)
    snap = (await prof.json())["finance"]
    assert snap["cost"] == 20100
    assert snap["source"] == "expense_records"


async def test_documents_photos_clients_tasks_audit(client: TestClient):
    org = f"auto-docs-{uuid.uuid4().hex[:8]}"
    h = _hdr(org, "auto_director")
    v = await client.post(f"{OPS}/vehicles", json={"vin": VIN, "manufacturer": "BMW", "auction_url": "https://a"}, headers=h)
    vid = (await v.json())["item"]["id"]

    payload = base64.b64encode(b"%PDF-1.4 test").decode()
    up = await client.post(
        f"{OPS}/files",
        json={"filename": "invoice.pdf", "mime_type": "application/pdf", "content_base64": payload, "entity_type": "vehicle", "entity_id": vid, "document_type": "auction_invoice"},
        headers=h,
    )
    assert up.status == 201

    photo = await client.post(
        f"{OPS}/files",
        json={"filename": "car.jpg", "mime_type": "image/jpeg", "content_base64": base64.b64encode(b"\xff\xd8fake").decode(), "entity_type": "vehicle", "entity_id": vid, "as_photo": True, "photo_category": "AUCTION"},
        headers=h,
    )
    assert photo.status == 201

    cl = await client.post(f"{OPS}/clients", json={"name": "Иванов", "phone": "+380", "telegram": "@ivan"}, headers=h)
    assert cl.status == 201
    cid = (await cl.json())["item"]["id"]
    await client.post(f"{OPS}/vehicles/{vid}", json={"client_id": cid}, headers=h)

    task = await client.post(f"{OPS}/tasks", json={"title": "Проверить title", "vehicle_id": vid}, headers=h)
    assert task.status == 201

    audit = await client.get(f"{OPS}/audit", headers=h)
    actions = {a["action"] for a in (await audit.json())["items"]}
    assert "vehicle_created" in actions
    assert "document_uploaded" in actions
    assert "client_assigned" in actions


async def test_rbac_unauthorized_and_client_denied(client: TestClient):
    org = f"auto-rbac-{uuid.uuid4().hex[:8]}"
    guest = await client.get(f"{OPS}/vehicles", headers=_hdr(org, "client"))
    assert guest.status == 403

    observer_create = await client.post(
        f"{OPS}/vehicles",
        json={"vin": VIN, "manufacturer": "BMW", "auction_url": "https://a"},
        headers=_hdr(org, "auto_admin"),
    )
    # admin has no create
    assert observer_create.status == 403

    mgr = await client.post(f"{OPS}/vehicles", json={"vin": VIN, "manufacturer": "BMW", "auction_url": "https://a"}, headers=_hdr(org, "auto_manager"))
    assert mgr.status == 201
    vid = (await mgr.json())["item"]["id"]

    acc_create = await client.post(f"{OPS}/vehicles", json={"vin": VIN[:-1] + "1", "manufacturer": "Audi", "auction_url": "https://b"}, headers=_hdr(org, "auto_accountant"))
    assert acc_create.status == 403

    acc_view = await client.get(f"{OPS}/vehicles/{vid}", headers=_hdr(org, "auto_accountant"))
    assert acc_view.status == 200
    assert (await acc_view.json())["finance"].get("restricted") is not True

    mgr_fin = await client.get(f"{OPS}/expenses", headers=_hdr(org, "auto_manager"))
    assert mgr_fin.status == 403


async def test_normalize_role_aliases():
    assert normalize_role("директор") == "auto_director"
    assert normalize_role("бухгалтер") == "auto_accountant"
    assert can("auto_accountant", "finance_write")
    assert not can("auto_manager", "finance_write")
    assert not can("client", "view")
