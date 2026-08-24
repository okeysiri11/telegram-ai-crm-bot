"""AGRO Production 1.0 — counterparties, deals, calculations, RBAC, intel honesty."""

from __future__ import annotations

import base64
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


TINY_PDF = b"%PDF-1.1\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"


async def test_health_sprint(client: TestClient):
    body = await (await client.get(f"{OPS}/health")).json()
    assert body["status"] == "ok"
    assert body["sprint"] == "agro-2.0"
    assert any(r["id"] == "agro_director" for r in body["roles"])
    assert any(r["id"] == "agro_accountant" for r in body["roles"])
    assert "client_secret" not in str(body).lower()
    assert "refresh_token" not in str(body).lower()


async def test_counterparty_contacts_and_roles(client: TestClient):
    org = f"org-agro-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    created = await client.post(
        f"{OPS}/entities/counterparty",
        json={"name": "Test Agro Partner", "types": ["farmer", "supplier"], "country": "UA"},
        headers=h,
    )
    assert created.status == 201
    item = (await created.json())["item"]
    assert "farmer" in item["types"] and "supplier" in item["types"]
    cid = item["id"]
    contact = await client.post(
        f"{OPS}/entities/contact",
        json={"full_name": "Иван Петров", "position": "Директор", "phone": "+380", "counterparty_id": cid},
        headers=h,
    )
    assert contact.status == 201
    rel = await (await client.get(f"{OPS}/entities/counterparty/{cid}/related", headers=h)).json()
    assert rel["related"]["contacts"]
    listed = await (await client.get(f"{OPS}/counterparties", headers=h)).json()
    assert any(i["id"] == cid for i in listed["items"])


async def test_deal_calculation_payment_shipment(client: TestClient):
    org = f"org-agro-d-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    cp = (await (await client.post(f"{OPS}/entities/counterparty", json={"name": "Test Agro Partner", "types": ["farmer", "supplier"]}, headers=h)).json())["item"]
    deal = (
        await (
            await client.post(
                f"{OPS}/entities/deal",
                json={"title": "Пшеница 100т", "counterparty_id": cp["id"], "crop": "Пшеница", "side": "buy", "quantity": 100, "unit": "т", "price": 200},
                headers=h,
            )
        ).json()
    )["item"]
    contract = (
        await (
            await client.post(
                f"{OPS}/entities/contract",
                json={"title": "Договор пшеницы", "counterparty_id": cp["id"], "deal_id": deal["id"]},
                headers=h,
            )
        ).json()
    )["item"]
    preview = await (
        await client.post(
            f"{OPS}/calculations/preview",
            json={"quantity": 100, "purchase_price": 200, "sale_price": 260, "transport": 1500, "storage": 500, "currency": "UAH"},
            headers=h,
        )
    ).json()
    totals = preview["item"]["totals"]
    assert totals["purchase_value"] == 20000
    assert totals["total_cost"] == 22000
    assert totals["sale_value"] == 26000
    assert totals["gross_profit"] == 4000
    assert totals["profit_per_tonne"] == 40
    assert preview["item"]["fx_note_ru"] == "Курс не подключён"
    calc = (
        await (
            await client.post(
                f"{OPS}/entities/calculation",
                json={
                    "title": "Расчёт пшеницы",
                    "counterparty_id": cp["id"],
                    "deal_id": deal["id"],
                    "contract_id": contract["id"],
                    "quantity": 100,
                    "purchase_price": 200,
                    "sale_price": 260,
                    "transport": 1500,
                    "storage": 500,
                },
                headers=h,
            )
        ).json()
    )["item"]
    assert calc["totals"]["margin_pct"] > 0
    pay = await client.post(
        f"{OPS}/entities/payment",
        json={"title": "Оплата поставщику", "amount": 5000, "currency": "UAH", "direction": "out", "deal_id": deal["id"], "counterparty_id": cp["id"]},
        headers=h,
    )
    assert pay.status == 201
    ship = await client.post(
        f"{OPS}/entities/shipment",
        json={"title": "Поставка пшеницы", "deal_id": deal["id"], "counterparty_id": cp["id"], "quantity": 100},
        headers=h,
    )
    assert ship.status == 201
    rel = await (await client.get(f"{OPS}/entities/deal/{deal['id']}/related", headers=h)).json()
    assert rel["related"]["calculations"]
    assert rel["related"]["contracts"]
    assert rel["related"]["payments"]
    assert rel["related"]["shipments"]


async def test_attachment_pdf(client: TestClient):
    org = f"org-agro-f-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    cp = (await (await client.post(f"{OPS}/entities/counterparty", json={"name": "Файловый"}, headers=h)).json())["item"]
    up = await client.post(
        f"{OPS}/files",
        json={
            "filename": "contract.pdf",
            "mime_type": "application/pdf",
            "content_base64": base64.b64encode(TINY_PDF).decode(),
            "entity_type": "counterparty",
            "entity_id": cp["id"],
            "doc_type": "contract",
        },
        headers=h,
    )
    assert up.status in {200, 201}
    fid = (await up.json())["item"]["id"]
    content = await client.get(f"{OPS}/files/{fid}/content", headers=h)
    assert content.status == 200
    bad = await client.post(
        f"{OPS}/files",
        json={"filename": "x.exe", "content_base64": base64.b64encode(b"MZ").decode(), "entity_type": "counterparty", "entity_id": cp["id"]},
        headers=h,
    )
    assert (await bad.json()).get("ok") is False


async def test_rbac_director_vs_accountant(client: TestClient):
    org = f"org-agro-rbac-{uuid.uuid4().hex[:8]}"
    director = _hdr(org, "agro_director")
    accountant = _hdr(org, "agro_accountant")
    cp = await client.post(f"{OPS}/entities/counterparty", json={"name": "Только директор"}, headers=accountant)
    assert (await cp.json()).get("error") == "forbidden"
    created = (await (await client.post(f"{OPS}/entities/counterparty", json={"name": "ОК"}, headers=director)).json())["item"]
    listed = await (await client.get(f"{OPS}/entities/counterparty", headers=accountant)).json()
    assert any(i["id"] == created["id"] for i in listed["items"])
    archive = await client.post(f"{OPS}/entities/counterparty/{created['id']}/archive", json={}, headers=accountant)
    assert (await archive.json()).get("error") == "forbidden"
    intel = await client.post(f"{OPS}/reports/generate", json={"kind": "morning"}, headers=accountant)
    assert (await intel.json()).get("error") == "forbidden"
    pay = await client.post(
        f"{OPS}/entities/payment",
        json={"title": "Оплата бухгалтера", "amount": 10, "currency": "UAH"},
        headers=accountant,
    )
    assert pay.status == 201
    deal = (await (await client.post(f"{OPS}/entities/deal", json={"title": "На утверждение"}, headers=director)).json())["item"]
    approve = await client.post(f"{OPS}/entities/deal/{deal['id']}", json={"status": "approved"}, headers=accountant)
    assert (await approve.json()).get("error") == "forbidden"
    ok = await client.post(f"{OPS}/entities/deal/{deal['id']}", json={"status": "approved"}, headers=director)
    assert ok.status == 200


async def test_tenant_isolation(client: TestClient):
    a, b = f"org-agro-a-{uuid.uuid4().hex[:6]}", f"org-agro-b-{uuid.uuid4().hex[:6]}"
    created = (await (await client.post(f"{OPS}/entities/counterparty", json={"name": "ONLY-A"}, headers=_hdr(a))).json())["item"]
    items = (await (await client.get(f"{OPS}/entities/counterparty", headers=_hdr(b))).json())["items"]
    assert all(i.get("name") != "ONLY-A" for i in items)
    other = await client.get(f"{OPS}/entities/counterparty/{created['id']}", headers=_hdr(b))
    assert (await other.json()).get("error") == "not_found"


async def test_providers_honest_and_no_fake_market(client: TestClient):
    org = f"org-agro-p-{uuid.uuid4().hex[:8]}"
    items = {i["id"]: i for i in (await (await client.get(f"{OPS}/providers", headers=_hdr(org))).json())["items"]}
    assert items["usda_wasde"]["status"] == "NOT_CONFIGURED"
    assert items["ua_stat"]["status"] == "NOT_CONFIGURED"
    assert items["manual_import"]["status"] == "LIVE"
    assert "Требуется подключение" in items["usda_wasde"]["note_ru"]


async def test_intel_import_dedupe_and_reports(client: TestClient):
    org = f"org-agro-i-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    first = await client.post(f"{OPS}/intel/import", json={"title": "WASDE note", "summary": "manual", "section": "world"}, headers=h)
    assert first.status in {200, 201}
    dup = await client.post(f"{OPS}/intel/import", json={"title": "WASDE note", "summary": "manual", "section": "world"}, headers=h)
    assert (await dup.json()).get("error") == "duplicate"
    r1 = await (await client.post(f"{OPS}/reports/generate", json={"kind": "morning"}, headers=h)).json()
    r2 = await (await client.post(f"{OPS}/reports/generate", json={"kind": "morning"}, headers=h)).json()
    assert r1["ok"] and r2["ok"]
    assert r2.get("deduplicated") is True
    assert r1["item"]["id"] == r2["item"]["id"]
    evening = await (await client.post(f"{OPS}/reports/generate", json={"kind": "evening"}, headers=h)).json()
    assert evening["ok"]
    empty_sections = [s for s in evening["item"]["sections"] if s["status"] == "NOT_CONFIGURED"]
    assert empty_sections, "unconfigured sections must stay honest"
    weekly = await (await client.post(f"{OPS}/reports/generate", json={"kind": "weekly"}, headers=h)).json()
    assert weekly["item"]["themes"]
    outlook = await (await client.post(f"{OPS}/reports/generate", json={"kind": "outlook"}, headers=h)).json()
    assert len(outlook["item"]["scenarios"]) == 3


async def test_scheduler_idempotent(client: TestClient):
    org = f"org-agro-s-{uuid.uuid4().hex[:8]}"
    from services.agro_ops import get_agro_ops_service

    svc = get_agro_ops_service()
    await svc.ensure_hydrated(org)
    first = await svc.run_report_sweep(org, kind="morning")
    second = await svc.run_report_sweep(org, kind="morning")
    assert first["ok"] and second["ok"]
    reports = (await (await client.get(f"{OPS}/reports?kind=morning", headers=_hdr(org))).json())["items"]
    assert len(reports) == 1


async def test_audit_log(client: TestClient):
    org = f"org-agro-aud-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    created = (await (await client.post(f"{OPS}/entities/counterparty", json={"name": "Аудит"}, headers=h)).json())["item"]
    await client.post(f"{OPS}/entities/counterparty/{created['id']}", json={"city": "Киев"}, headers=h)
    activity = (await (await client.get(f"{OPS}/activity", headers=h)).json())["items"]
    actions = {a.get("action") for a in activity}
    assert "counterparty_created" in actions
    assert "edited" in actions
    blob = str(activity)
    assert "password" not in blob.lower()
    assert "token" not in blob.lower()


async def test_notifications_and_channels(client: TestClient):
    org = f"org-agro-n-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    await client.post(f"{OPS}/entities/payment", json={"title": "Платёж", "amount": 1}, headers=h)
    notes = (await (await client.get(f"{OPS}/notifications", headers=h)).json())["items"]
    assert notes
    ch = await (await client.get(f"{OPS}/channels", headers=h)).json()
    assert ch["channels"]["in_app"]["connected"] is True
    assert ch["channels"]["telegram"]["connected"] in {True, False}
    if not ch["channels"]["telegram"]["connected"]:
        assert ch["channels"]["telegram"]["status"] == "NOT_CONFIGURED"


async def test_ask_ai_data_gap(client: TestClient):
    org = f"org-agro-ai-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    r = await (await client.post(f"{OPS}/ai/ask", json={"question": "Почему это важно для экспорта кукурузы?", "context": {"section": "trade"}}, headers=h)).json()
    assert r["ok"]
    assert "DATA GAP" in r["item"]["answer_ru"] or r["item"]["data_gaps"]
