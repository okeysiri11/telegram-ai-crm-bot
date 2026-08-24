"""Sprint AUTO 1.2 — customs / broker / import VAT / certification desk."""

from __future__ import annotations

import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.auto_enterprise.api.register import register_auto_enterprise_routes
from services.auto_ops import reset_auto_ops_for_tests
from services.auto_ops.customs_catalog import calculate_customs
from services.auto_ops.rbac import can

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


async def _vehicle(client: TestClient, org: str, vin: str = VIN, role: str = "auto_manager") -> str:
    res = await client.post(
        f"{OPS}/vehicles",
        json={"vin": vin, "manufacturer": "BMW", "model": "X5", "year": 2013, "fuel_type": "petrol", "engine": "2993", "auction_url": "https://a"},
        headers=_hdr(org, role),
    )
    assert res.status == 201, await res.text()
    return (await res.json())["item"]["id"]


async def test_health_is_auto_1_2(client: TestClient):
    res = await client.get(f"{OPS}/health")
    body = await res.json()
    assert body["sprint"] in {"AUTO_1.2", "AUTO_1.3", "AUTO_1.4", "AUTO_1.5", "AUTO_1.6", "AUTO_1.7", "AUTO_1.8", "AUTO_1.8.5"}
    assert body["telegram"]["status"] in {"prepared", "live"}
    intents = {i["command"] for i in body["telegram"]["intents"]}
    assert "/customs <VIN>" in intents
    assert "/vat <VIN>" in intents
    assert "/logistics <VIN>" in intents
    assert "Новый бот не строится" in body["telegram"]["message_ru"]


def test_calculation_engine_org_rates_never_invents():
    incomplete = calculate_customs(customs_value=None, fx_rate_to_uah=41.5, engine_cc=2993, year=2013)
    assert incomplete["ok"] is False
    assert "customs_value" in incomplete["incomplete"]
    no_fx = calculate_customs(customs_value=18500, engine_cc=2993, year=2013)
    assert no_fx["ok"] is False
    assert "fx_rate_to_uah" in no_fx["incomplete"]
    ok = calculate_customs(
        customs_value=18500,
        currency="USD",
        fx_rate_to_uah=41.5,
        engine_cc=2993,
        fuel_type="petrol",
        year=2013,
        broker_fee_uah=8000,
        today_year=2026,
    )
    assert ok["ok"] is True
    assert ok["customs_value_uah"] == 767750.0
    assert ok["duty_uah"] == 76775.0
    assert ok["excise_uah"] == 224475.0
    assert ok["import_vat_uah"] == 213800.0
    assert ok["grand_total_uah"] == 523050.0
    assert ok["source"] == "org_rates"
    assert "Гостаможни" in ok["disclaimer_ru"]
    assert ok["fx_source_label_ru"] == "Введено вручную"


async def test_case_crud_vehicle_link_answers_and_status(client: TestClient):
    org = f"auto-c12-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    vid = await _vehicle(client, org)
    created = await client.post(f"{OPS}/customs/cases", json={"vehicle_id": vid, "status": "DOCUMENTS_PREP"}, headers=h)
    assert created.status == 201, await created.text()
    case = (await created.json())["item"]
    cid = case["id"]
    assert case["vehicle_id"] == vid
    assert case["live_customs_api"] is False
    answers = case["answers"]
    assert answers["happening"]
    assert answers["next_stage"]
    assert "Где" not in answers  # operational keys, not question text

    conflict = await client.post(f"{OPS}/customs/cases", json={"vehicle_id": vid}, headers=h)
    assert conflict.status == 409

    bad = await client.post(f"{OPS}/customs/cases/{cid}", json={"status": "flying"}, headers=h)
    assert bad.status == 400

    ok = await client.post(f"{OPS}/customs/cases/{cid}", json={"status": "PAYMENT_PENDING", "location_current": "Одесса, таможня"}, headers=h)
    assert ok.status == 200
    body = await ok.json()
    assert body["item"]["status"] == "PAYMENT_PENDING"
    assert body["item"]["answers"]["where"] == "Одесса, таможня"
    steps = {s["id"]: s["state"] for s in body["item"]["pipeline"]}
    assert steps["pay"] == "current"

    listed = await client.get(f"{OPS}/customs/cases?tab=pay&q=BMW", headers=h)
    assert listed.status == 200
    assert any(x["id"] == cid for x in (await listed.json())["items"])

    profile = await client.get(f"{OPS}/vehicles/{vid}", headers=h)
    customs = (await profile.json())["customs"]
    assert customs["case"]["id"] == cid
    assert customs["case"]["status"] == "PAYMENT_PENDING"


async def test_calculation_payments_vat_multicurrency(client: TestClient):
    org = f"auto-vat-{uuid.uuid4().hex[:8]}"
    mgr = _hdr(org)
    acc = _hdr(org, "auto_accountant")
    vid = await _vehicle(client, org)
    created = await client.post(
        f"{OPS}/customs/cases",
        json={"vehicle_id": vid, "customs_value": 18500, "currency": "USD", "fx_rate_to_uah": 41.5, "engine_cc": 2993, "year": 2013, "fuel_type": "petrol", "broker_fee_uah": 8000},
        headers=mgr,
    )
    cid = (await created.json())["item"]["id"]
    calc = await client.post(f"{OPS}/customs/cases/{cid}/calculate", json={}, headers=mgr)
    assert calc.status == 200, await calc.text()
    cbody = await calc.json()
    assert cbody["calculation"]["ok"] is True
    assert cbody["calculation"]["import_vat_uah"] == 213800.0

    still_forbidden = await client.post(f"{OPS}/expenses", json={"vehicle_id": vid, "category": "PURCHASE", "amount": 1000}, headers=mgr)
    assert still_forbidden.status == 403

    duty = await client.post(
        f"{OPS}/expenses",
        json={"vehicle_id": vid, "customs_id": cid, "category": "DUTY", "amount": 76775, "currency": "UAH", "exchange_rate": 1, "payment_status": "planned"},
        headers=mgr,
    )
    assert duty.status == 201, await duty.text()

    vat = await client.post(
        f"{OPS}/expenses",
        json={"vehicle_id": vid, "customs_id": cid, "category": "IMPORT_VAT", "amount": 50000, "currency": "UAH", "exchange_rate": 1, "payment_status": "paid"},
        headers=acc,
    )
    assert vat.status == 201

    det = await client.get(f"{OPS}/customs/cases/{cid}", headers=acc)
    item = (await det.json())["item"]
    assert item["payments"]["paid"] == 50000
    assert item["payments"]["import_vat_paid"] == 50000
    assert item["accounting"]["vat"]["calculated_uah"] == 213800.0
    assert "by_currency" in item["payments"]
    assert item["payments"]["fx_source_label_ru"] == "Введено вручную"


async def test_checklist_preview_and_missing_docs(client: TestClient):
    org = f"auto-docs12-{uuid.uuid4().hex[:8]}"
    mgr = _hdr(org)
    vid = await _vehicle(client, org)
    created = await client.post(f"{OPS}/customs/cases", json={"vehicle_id": vid}, headers=mgr)
    cid = (await created.json())["item"]["id"]
    missing = (await created.json())["item"]["checklist"]["missing"]
    assert any(m["document_type"] == "invoice" for m in missing)

    doc = await client.post(
        f"{OPS}/documents",
        json={"owner_type": "customs", "customs_id": cid, "vehicle_id": vid, "file_name": "inv.pdf", "document_type": "invoice", "file_id": "file-1"},
        headers=mgr,
    )
    assert doc.status == 201
    det = await client.get(f"{OPS}/customs/cases/{cid}", headers=mgr)
    check = (await det.json())["item"]["checklist"]
    invoice = next(i for i in check["items"] if i["document_type"] == "invoice")
    assert invoice["present"] is True
    assert invoice["preview"]["file_id"] == "file-1"
    assert any(m["document_type"] == "customs_declaration" for m in check["missing"])


async def test_brokers_certification_registration_timeline(client: TestClient):
    org = f"auto-brk-{uuid.uuid4().hex[:8]}"
    mgr = _hdr(org)
    vid = await _vehicle(client, org)
    broker = await client.post(f"{OPS}/customs/brokers", json={"company_name": "Odesa Broker", "type": "customs_broker", "country": "UA"}, headers=mgr)
    assert broker.status == 201
    bid = (await broker.json())["item"]["id"]
    created = await client.post(f"{OPS}/customs/cases", json={"vehicle_id": vid, "broker_id": bid}, headers=mgr)
    cid = (await created.json())["item"]["id"]
    assert (await created.json())["item"]["broker_name"] == "Odesa Broker"

    cert = await client.post(f"{OPS}/customs/cases/{cid}", json={"status": "CERTIFICATION", "cert_status": "IN_PROGRESS", "cert_body": "Lab A"}, headers=mgr)
    assert cert.status == 200
    assert (await cert.json())["item"]["certification"]["status"] == "IN_PROGRESS"

    reg = await client.post(f"{OPS}/customs/cases/{cid}", json={"status": "REGISTRATION_PREP", "reg_status": "DOCS_READY", "mreo_office": "МРЕО Одеса"}, headers=mgr)
    assert (await reg.json())["item"]["registration"]["status"] == "DOCS_READY"

    audit = await client.get(f"{OPS}/audit", headers=_hdr(org, "auto_director"))
    actions = {a["action"] for a in (await audit.json())["items"]}
    assert "customs_case_created" in actions
    assert "broker_created" in actions
    assert "certification_updated" in actions or "customs_status_changed" in actions


async def test_rbac_accountant_sees_customs_admin_cannot_create(client: TestClient):
    org = f"auto-rbac12-{uuid.uuid4().hex[:8]}"
    vid = await _vehicle(client, org)
    mgr = _hdr(org)
    created = await client.post(f"{OPS}/customs/cases", json={"vehicle_id": vid}, headers=mgr)
    assert created.status == 201

    acc = await client.get(f"{OPS}/customs/cases", headers=_hdr(org, "auto_accountant"))
    assert acc.status == 200
    assert (await acc.json())["total"] == 1
    item = (await acc.json())["items"][0]
    assert "accounting" in item

    admin_create = await client.post(f"{OPS}/customs/cases", json={"vehicle_id": vid, "reassign": True}, headers=_hdr(org, "auto_admin"))
    assert admin_create.status == 403

    guest = await client.get(f"{OPS}/customs/cases", headers=_hdr(org, "client"))
    assert guest.status == 403
    assert can("auto_manager", "create")
    assert not can("auto_accountant", "create")


async def test_demo_requires_confirm_and_is_labelled(client: TestClient):
    org = f"auto-demo12-{uuid.uuid4().hex[:8]}"
    h = _hdr(org, "auto_director")
    denied = await client.post(f"{OPS}/customs/demo", json={}, headers=h)
    assert denied.status == 400
    ok = await client.post(f"{OPS}/customs/demo", json={"confirm_demo": True}, headers=h)
    assert ok.status == 201, await ok.text()
    body = await ok.json()
    assert body["demo"] is True
    assert body["vehicle"]["model"] == "X5"
    assert body["case"]["is_demo"] is True
    assert "Демо" in (body["label_ru"] or "")
    missing_types = {m["document_type"] for m in body["case"]["checklist"]["missing"]}
    assert "customs_declaration" in missing_types
    assert body["case"]["calculation"]["ok"] is True
    assert body["case"]["answers"]["to_pay"] is not None
