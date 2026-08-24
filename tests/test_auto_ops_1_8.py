"""Sprint AUTO 1.8 — customs Telegram, state machine, audit, landed cost, analytics."""

from __future__ import annotations

import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.auto_enterprise.api.register import register_auto_enterprise_routes
from services.auto_ops import reset_auto_ops_for_tests
from services.auto_ops.customs_catalog import transition_allowed

OPS = "/api/auto-ops/v1"
VIN = "1HGCM82633A004352"
PNG_1PX = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="


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
    payload = {"vin": vin, "manufacturer": "BMW", "model": "X5", "year": 2013, "fuel_type": "petrol", "engine": "2993", **body}
    res = await client.post(f"{OPS}/vehicles", json=payload, headers=_hdr(org, "auto_manager"))
    assert res.status == 201, await res.text()
    return (await res.json())["item"]["id"]


async def _bind(client: TestClient, org: str, telegram_id: int, role: str, label: str) -> None:
    res = await client.post(
        f"{OPS}/telegram/members",
        json={"telegram_id": telegram_id, "role": role, "label": label},
        headers=_hdr(org, "auto_director"),
    )
    assert res.status in {200, 201}, await res.text()


async def _in(client: TestClient, telegram_id: int, text: str = "", extra: dict | None = None, callback_data: str | None = None) -> tuple[int, dict]:
    body: dict = {"telegram_id": telegram_id, "text": text}
    if extra:
        body["extra"] = extra
    if callback_data:
        body["callback_data"] = callback_data
    res = await client.post(f"{OPS}/telegram/inbound", json=body, headers=_hdr("default", "auto_director"))
    return res.status, await res.json()


async def test_auto_ops_1_8_health_and_transitions(client: TestClient):
    res = await client.get(f"{OPS}/health")
    body = await res.json()
    assert body["sprint"] in {"AUTO_1.8", "AUTO_1.8.5"}
    assert body["private"] is True
    assert "Новый бот не строится" in body["telegram"]["message_ru"]
    intents = {i["command"] for i in body["telegram"]["intents"]}
    assert "/customspay <VIN>" in intents
    assert "/customsdoc <VIN>" in intents
    assert "/customsstatus <VIN>" in intents
    catalogs = (await (await client.get(f"{OPS}/catalogs", headers=_hdr("auto-a18-x"))).json())["catalogs"]
    assert catalogs["customs_policy"]["correction_requires_reason"] is True
    assert transition_allowed("DOCUMENTS_PREP", "PAYMENT_PENDING", telegram=False) is True
    assert transition_allowed("DOCUMENTS_PREP", "PAYMENT_PENDING", telegram=True) is False
    assert transition_allowed("REGISTERED", "SUBMITTED", telegram=False) is False
    assert transition_allowed("REGISTERED", "DECLARATION_SUBMITTED", telegram=False) is False


async def test_state_machine_correction_audit_and_search(client: TestClient):
    org = f"auto-a18-{uuid.uuid4().hex[:8]}"
    vid = await _vehicle(client, org)
    h = _hdr(org, "auto_manager")
    created = await client.post(f"{OPS}/customs/cases", json={"vehicle_id": vid, "status": "DOCUMENTS_PREP", "declaration_number": "MD-18-AAA"}, headers=h)
    assert created.status == 201, await created.text()
    cid = (await created.json())["item"]["id"]

    skip = await client.post(f"{OPS}/customs/cases/{cid}", json={"status": "PAYMENT_PENDING"}, headers=h)
    assert skip.status == 200, await skip.text()

    to_reg = await client.post(f"{OPS}/customs/cases/{cid}", json={"status": "REGISTERED"}, headers=h)
    assert to_reg.status == 200
    back = await client.post(f"{OPS}/customs/cases/{cid}", json={"status": "DECLARATION_SUBMITTED"}, headers=h)
    assert back.status == 400
    assert "Недопустимый переход" in (await back.json())["message_ru"]

    acc = await client.post(f"{OPS}/customs/cases/{cid}", json={"status": "PAID"}, headers=_hdr(org, "auto_accountant"))
    assert acc.status == 403

    admin_no = await client.post(f"{OPS}/customs/cases/{cid}", json={"status": "SUBMITTED"}, headers=_hdr(org, "auto_admin"))
    assert admin_no.status in {400, 403}

    corr = await client.post(
        f"{OPS}/customs/cases/{cid}",
        json={"status": "SUBMITTED", "correction_reason": "Ошибка брокера", "correction_at": "2026-08-01T12:00:00Z"},
        headers=_hdr(org, "auto_director", principal="dir-18"),
    )
    assert corr.status == 200, await corr.text()
    assert (await corr.json())["item"]["status"] == "SUBMITTED"

    broker = await client.post(f"{OPS}/customs/brokers", json={"company_name": "Odesa Broker 18", "type": "customs_broker"}, headers=h)
    bid = (await broker.json())["item"]["id"]
    await client.post(f"{OPS}/customs/cases/{cid}", json={"broker_id": bid, "cert_number": "CERT-18", "reg_status": "REGISTERED"}, headers=h)

    listed = await (await client.get(f"{OPS}/search?q=MD-18-AAA", headers=_hdr(org))).json()
    kinds = {i["kind"] for i in listed["items"]}
    assert "customs" in kinds or "declaration" in kinds

    audit = await (await client.get(f"{OPS}/audit", headers=_hdr(org))).json()
    actions = {a["action"] for a in audit["items"]}
    assert "customs_case_created" in actions
    assert "customs_status_changed" in actions or "customs_status_corrected" in actions
    assert "customs_status_corrected" in actions
    assert "declaration_entered" in actions or "customs_case_created" in actions
    assert "broker_assigned" in actions or "customs_broker_changed" in actions
    assert "certificate_added" in actions or "certification_updated" in actions
    assert "registration_completed" in actions


async def test_telegram_customs_pay_doc_status(client: TestClient):
    org = f"auto-a18-{uuid.uuid4().hex[:8]}"
    vid = await _vehicle(client, org)
    h = _hdr(org, "auto_manager")
    created = await client.post(f"{OPS}/customs/cases", json={"vehicle_id": vid, "status": "DOCUMENTS_PREP"}, headers=h)
    cid = (await created.json())["item"]["id"]
    await _bind(client, org, 181001, "auto_accountant", "Бухгалтер")
    await _bind(client, org, 181002, "auto_manager", "Менеджер")

    st, pay = await _in(client, 181001, f"/customspay {VIN}", extra={"category": "DUTY", "amount": 1200, "currency": "UAH", "comment": "мито"})
    assert st == 200, pay
    assert pay["ok"] is True
    assert pay.get("confirmed") is False
    expense = pay["item"]
    assert expense["payment_status"] == "planned"
    assert expense["customs_id"] == cid

    st, conf = await _in(client, 181001, f"/customspay {VIN}", extra={"confirm": True, "expense_id": expense["id"]})
    assert st == 200, conf
    assert conf.get("confirmed") is True
    assert conf["item"]["payment_status"] == "paid"

    st, blocked = await _in(client, 181001, f"/customsstatus {VIN}", extra={"status": "SUBMITTED"})
    assert blocked.get("ok") is False

    st, nxt = await _in(client, 181002, f"/customsstatus {VIN}")
    assert nxt["ok"] is True
    assert "SUBMITTED" in (nxt.get("allowed_next") or [])
    assert "PAYMENT_PENDING" not in (nxt.get("allowed_next") or [])

    st, bad = await _in(client, 181002, f"/customsstatus {VIN}", extra={"status": "PAYMENT_PENDING"})
    assert bad.get("ok") is False

    st, okst = await _in(client, 181002, f"/customsstatus {VIN}", extra={"status": "SUBMITTED"})
    assert okst.get("ok") is True, okst
    assert okst["item"]["status"] == "SUBMITTED"

    st, doc = await _in(
        client,
        181002,
        f"/customsdoc {VIN}",
        extra={"document_type": "customs_declaration", "filename": "md.pdf", "mime_type": "application/pdf", "content_base64": PNG_1PX},
    )
    assert doc.get("ok") is True, doc
    assert doc["item"].get("customs_id") == cid or doc["item"].get("vehicle_id") == vid


async def test_tenant_workspace_isolation_and_summary(client: TestClient):
    org_a = f"auto-a18-{uuid.uuid4().hex[:8]}"
    org_b = f"auto-a18-{uuid.uuid4().hex[:8]}"
    vid_a = await _vehicle(client, org_a, vin="1HGCM82633A004352")
    vid_b = await _vehicle(client, org_b, vin="1HGCM82633A004353")
    a = await client.post(f"{OPS}/customs/cases", json={"vehicle_id": vid_a, "workspace_id": "ws-a", "declaration_number": "MD-A"}, headers=_hdr(org_a, "auto_manager"))
    b = await client.post(f"{OPS}/customs/cases", json={"vehicle_id": vid_b, "workspace_id": "ws-b", "declaration_number": "MD-B"}, headers=_hdr(org_b, "auto_manager"))
    assert a.status == 201 and b.status == 201
    cid = (await a.json())["item"]["id"]
    listed_a = await (await client.get(f"{OPS}/customs/cases?workspace_id=ws-a", headers=_hdr(org_a))).json()
    assert all(i.get("workspace_id") == "ws-a" for i in listed_a["items"])
    assert all(i.get("declaration_number") != "MD-B" for i in listed_a["items"])
    other = await (await client.get(f"{OPS}/customs/cases?workspace_id=ws-a", headers=_hdr(org_b))).json()
    assert other["items"] == [] or all(i.get("declaration_number") != "MD-A" for i in other["items"])
    summary = await (await client.get(f"{OPS}/customs/cases/{cid}/summary?workspace_id=ws-a", headers=_hdr(org_a))).json()
    assert summary["ok"] is True
    assert summary["item"]["title_ru"] == "Сводка по растаможке"
    assert summary["item"]["vin"]
    assert summary["item"]["declaration"] == "MD-A"
    leaked = await client.get(f"{OPS}/customs/cases/{cid}/summary?workspace_id=ws-a", headers=_hdr(org_b))
    assert leaked.status in {404, 200}
    if leaked.status == 200:
        assert (await leaked.json()).get("ok") is False


async def test_landed_cost_profit_cashflow_no_double_count(client: TestClient):
    org = f"auto-a18-{uuid.uuid4().hex[:8]}"
    vid = await _vehicle(client, org, status="SOLD", sale_price_actual=30000)
    h = _hdr(org)
    acc = _hdr(org, "auto_accountant")
    created = await client.post(f"{OPS}/customs/cases", json={"vehicle_id": vid, "status": "CLEARED"}, headers=_hdr(org, "auto_manager"))
    cid = (await created.json())["item"]["id"]
    await client.post(f"{OPS}/expenses", json={"vehicle_id": vid, "category": "PURCHASE", "amount": 18000, "currency": "USD", "payment_status": "paid"}, headers=acc)
    await client.post(f"{OPS}/expenses", json={"vehicle_id": vid, "category": "AUCTION_FEE", "amount": 500, "currency": "USD", "payment_status": "paid"}, headers=acc)
    await client.post(f"{OPS}/expenses", json={"vehicle_id": vid, "category": "SEA_FREIGHT", "amount": 1500, "currency": "USD", "payment_status": "paid"}, headers=acc)
    pay = await client.post(f"{OPS}/customs/cases/{cid}/payments", json={"category": "DUTY", "amount": 2000, "currency": "USD"}, headers=acc)
    assert pay.status in {200, 201}, await pay.text()
    eid = (await pay.json())["item"]["id"]
    assert (await pay.json())["item"]["payment_status"] == "planned"
    conf = await client.post(f"{OPS}/customs/cases/{cid}/payments/{eid}/confirm", json={}, headers=acc)
    assert conf.status == 200
    await client.post(f"{OPS}/expenses", json={"vehicle_id": vid, "category": "REPAIR", "amount": 800, "currency": "USD", "payment_status": "paid"}, headers=acc)

    veh = await (await client.get(f"{OPS}/vehicles/{vid}", headers=h)).json()
    landed = veh["finance"]["landed"]
    assert landed["lines"]["purchase"] == 18000
    assert landed["lines"]["auction_fee"] == 500
    assert landed["lines"]["logistics"] == 1500
    assert landed["lines"]["customs_duty"] == 2000
    assert landed["selling_costs"] == 800
    assert landed["landed_cost"] == 22000
    assert veh["finance"]["actual_profit"] == 7200
    assert veh["finance"]["cost"] == 22800

    cf = await (await client.get(f"{OPS}/analytics/cashflow", headers=h)).json()
    outgoing = sum(float(r.get("outgoing") or 0) for r in cf.get("items") or [])
    assert outgoing == 22800

    econ = await (await client.get(f"{OPS}/analytics/economics", headers=h)).json()
    row = next(r for r in econ["items"] if r["vehicle_id"] == vid)
    assert row["sold"] is True
    assert row["landed_cost"] == 22000
    assert row["profit"] == 7200

    export = await client.get(f"{OPS}/analytics/export?kind=customs_cases", headers=h)
    assert export.status == 200
    assert "csv" in export.content_type
    text = (await export.read()).decode("utf-8")
    assert "VIN" in text


async def test_director_customs_analytics_real_records_only(client: TestClient):
    org = f"auto-a18-{uuid.uuid4().hex[:8]}"
    vid = await _vehicle(client, org)
    h = _hdr(org)
    created = await client.post(f"{OPS}/customs/cases", json={"vehicle_id": vid, "status": "DOCUMENTS_PREP"}, headers=_hdr(org, "auto_manager"))
    cid = (await created.json())["item"]["id"]
    empty = await (await client.get(f"{OPS}/analytics/customs", headers=h)).json()
    assert empty["metrics"]["avg_customs_duration"] is None
    await client.post(f"{OPS}/customs/cases/{cid}", json={"status": "CLEARED", "duty_uah": 1000, "excise_uah": 2000, "import_vat_uah": 3000, "state_total_uah": 6000}, headers=_hdr(org, "auto_manager"))
    hold = await client.post(f"{OPS}/customs/cases/{cid}", json={"status": "ON_HOLD"}, headers=_hdr(org, "auto_manager"))
    assert hold.status == 200
    data = await (await client.get(f"{OPS}/analytics/customs", headers=h)).json()
    assert data["from_records"] is True
    assert data["metrics"]["avg_customs_duration"] is not None
    assert data["metrics"]["avg_duty"] == 1000
    assert data["metrics"]["vehicles_delayed"] == 1
    assert data["metrics"]["blocked_vehicles"] == 0
