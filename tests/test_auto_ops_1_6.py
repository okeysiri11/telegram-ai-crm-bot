"""Sprint AUTO 1.6 — document OS, packages, generation drafts, Telegram /docs."""

from __future__ import annotations

import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.auto_enterprise.api.register import register_auto_enterprise_routes
from services.auto_ops import reset_auto_ops_for_tests
from services.auto_ops.documents_catalog import LEGAL_DISCLAIMER_RU

OPS = "/api/auto-ops/v1"
VIN = "1HGCM82633A004352"
VIN_B = "WBAFR9C50DD123456"
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


def _hdr(org: str, role: str = "auto_director", principal: str | None = None) -> dict[str, str]:
    h = {"X-Organization-Id": org, "X-Role": role}
    if principal:
        h["X-Principal"] = principal
    return h


async def _vehicle(client: TestClient, org: str, vin: str = VIN, **body) -> str:
    payload = {"vin": vin, "manufacturer": "BMW", "model": "X5", "year": 2013, **body}
    res = await client.post(f"{OPS}/vehicles", json=payload, headers=_hdr(org))
    assert res.status == 201, await res.text()
    return (await res.json())["item"]["id"]


async def _bind(client: TestClient, org: str, telegram_id: int, role: str, label: str) -> None:
    res = await client.post(
        f"{OPS}/telegram/members",
        json={"telegram_id": telegram_id, "role": role, "label": label},
        headers=_hdr(org),
    )
    assert res.status in {200, 201}, await res.text()


async def test_auto_ops_1_6_health(client: TestClient):
    res = await client.get(f"{OPS}/health")
    body = await res.json()
    assert body["sprint"] in {"AUTO_1.6", "AUTO_1.7", "AUTO_1.8", "AUTO_1.8.5"}
    assert body["private"] is True
    assert "Новый бот не строится" in body["telegram"]["message_ru"]
    catalogs = (await (await client.get(f"{OPS}/catalogs", headers=_hdr("auto-a16-x"))).json())["catalogs"]
    assert catalogs["registration_template_configurable"] is True
    assert catalogs["signature_provider"] is None
    assert catalogs["ocr_mandatory"] is False


async def test_individual_client_aliases_and_representative(client: TestClient):
    org = f"auto-a16-{uuid.uuid4().hex[:8]}"
    res = await client.post(
        f"{OPS}/clients",
        json={
            "full_name": "Іван Петренко",
            "phone": "+380501112233",
            "email": "ivan@example.com",
            "passport": "AB123456",
            "tax_number": "1234567890",
            "address": "Київ",
            "representative": "Олена Петренко",
        },
        headers=_hdr(org),
    )
    assert res.status == 201, await res.text()
    item = (await res.json())["item"]
    assert item["name"] == "Іван Петренко"
    assert item["tax_id"] == "1234567890"
    assert item["passport_ref"] == "AB123456"
    assert item["representative"] == "Олена Петренко"
    hidden = await (await client.get(f"{OPS}/clients/{item['id']}", headers=_hdr(org, "auto_manager"))).json()
    assert hidden["item"]["tax_id"] == "***"
    assert hidden["item"]["representative"] == "Олена Петренко"


async def test_sale_and_registration_packages(client: TestClient):
    org = f"auto-a16-{uuid.uuid4().hex[:8]}"
    vid = await _vehicle(client, org)
    sale = await (await client.get(f"{OPS}/documents/packages?vehicle_id={vid}&kind=sale", headers=_hdr(org))).json()
    assert sale["ok"] is True
    assert sale["status_ru"] == "НЕ ГОТОВО"
    assert any("ИНН" in m for m in sale["missing"])
    reg = await (await client.get(f"{OPS}/documents/packages?vehicle_id={vid}&kind=registration", headers=_hdr(org))).json()
    assert reg["configurable"] is True
    note = (reg.get("note_ru") or "").lower()
    assert "настраива" in note or "юридич" in note


async def test_templates_and_generate_draft_not_legal(client: TestClient):
    org = f"auto-a16-{uuid.uuid4().hex[:8]}"
    vid = await _vehicle(client, org)
    listed = await (await client.get(f"{OPS}/documents/templates", headers=_hdr(org))).json()
    stages = {s["id"] for s in listed["stages"]}
    assert {"purchase_us", "purchase_ge", "logistics", "customs", "sale_person", "sale_company", "registration"} <= stages
    created = await client.post(
        f"{OPS}/documents/generate",
        json={"template_id": "sale_agreement_draft", "vehicle_id": vid},
        headers=_hdr(org),
    )
    assert created.status == 201, await created.text()
    body = await created.json()
    assert body["draft"] is True
    assert body["item"]["workflow_status"] == "DRAFT"
    assert LEGAL_DISCLAIMER_RU in body["legal_disclaimer_ru"]
    assert "черновик" in body["message_ru"].lower() or "шаблон" in body["message_ru"].lower()


async def test_workflow_signature_manual_and_vin_conflict(client: TestClient):
    org = f"auto-a16-{uuid.uuid4().hex[:8]}"
    vid = await _vehicle(client, org)
    vid_b = await _vehicle(client, org, VIN_B, manufacturer="Audi", model="A6")
    doc = await client.post(
        f"{OPS}/documents",
        json={"vehicle_id": vid, "document_type": "invoice", "file_name": f"{VIN_B}-invoice.pdf", "document_number": "INV-1"},
        headers=_hdr(org),
    )
    body = await doc.json()
    assert doc.status == 201
    assert body.get("warning") is True
    assert body.get("code") == "vin_conflict"
    did = body["item"]["id"]
    assert body["item"]["vehicle_id"] == vid
    relink = await client.post(f"{OPS}/documents/{did}", json={"vehicle_id": vid_b, "confirm_relink": True}, headers=_hdr(org))
    assert relink.status == 200
    st = await client.post(
        f"{OPS}/documents/{did}/status",
        json={"workflow_status": "REVIEW", "signature_status": "WAITING"},
        headers=_hdr(org),
    )
    assert st.status == 200
    item = (await st.json())["item"]
    assert item["workflow_status"] == "REVIEW"
    assert item["signature_status"] == "WAITING"
    verify = await client.post(
        f"{OPS}/documents/{did}/status",
        json={"finance_verify": "VERIFIED"},
        headers=_hdr(org, "auto_accountant"),
    )
    assert verify.status == 200
    mgr = await client.post(
        f"{OPS}/documents/{did}/status",
        json={"finance_verify": "REJECTED"},
        headers=_hdr(org, "auto_manager"),
    )
    assert mgr.status == 403


async def test_tenant_isolation_and_csv_export(client: TestClient):
    a = f"auto-a16-{uuid.uuid4().hex[:8]}"
    b = f"auto-a16-{uuid.uuid4().hex[:8]}"
    vid = await _vehicle(client, a)
    await client.post(
        f"{OPS}/documents",
        json={"vehicle_id": vid, "document_type": "bill_of_lading", "file_name": "bl.pdf"},
        headers=_hdr(a),
    )
    other = await (await client.get(f"{OPS}/documents?vin={VIN}", headers=_hdr(b))).json()
    assert other.get("total") == 0 or not other.get("items")
    desk = await (await client.get(f"{OPS}/documents/desk", headers=_hdr(a))).json()
    assert desk["kpis"]["total"] >= 1
    export = await client.get(f"{OPS}/documents/export", headers=_hdr(a))
    assert export.status == 200
    assert "csv" in export.headers.get("Content-Type", "")
    csv_text = await export.text()
    assert "VIN" in csv_text


async def test_telegram_docs_and_file_rbac(client: TestClient):
    org = f"auto-a16-{uuid.uuid4().hex[:8]}"
    await _vehicle(client, org)
    await _bind(client, org, 61001, "auto_director", "Директор")
    await _bind(client, org, 61002, "auto_manager", "Менеджер")
    res = await client.post(f"{OPS}/telegram/inbound", json={"telegram_id": 61001, "text": f"/docs {VIN}"}, headers=_hdr(org))
    body = await res.json()
    assert res.status == 200, body
    assert "Документы:" in body["message_ru"]
    labels = [b["text"] for row in (body.get("keyboard") or []) for b in row]
    assert "Открыть досье" in labels
    assert "Добавить документ" in labels
    guest = await client.post(f"{OPS}/telegram/inbound", json={"telegram_id": 999111, "text": f"/docs {VIN}"}, headers=_hdr(org))
    assert guest.status == 403
    saved = await client.post(
        f"{OPS}/telegram/inbound",
        json={
            "telegram_id": 61002,
            "text": f"/doc {VIN} bill_of_lading",
            "extra": {"content_base64": PNG_1PX, "filename": "bl.png", "mime_type": "image/png"},
        },
        headers=_hdr(org),
    )
    saved_body = await saved.json()
    assert saved.status == 200, saved_body
    assert "сохранён" in saved_body["message_ru"].lower() or "привязан" in saved_body["message_ru"].lower()


async def test_status_warning_does_not_hard_block(client: TestClient):
    org = f"auto-a16-{uuid.uuid4().hex[:8]}"
    vid = await _vehicle(client, org)
    res = await client.post(f"{OPS}/vehicles/{vid}", json={"status": "READY_FOR_SALE"}, headers=_hdr(org))
    body = await res.json()
    assert res.status == 200
    assert body.get("warning") is True
    assert body["item"]["status"] == "READY_FOR_SALE"
