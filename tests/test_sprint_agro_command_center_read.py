"""AGRO Command Center aggregated read, tenant isolation, currency, export, audit."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

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


def _hdr(org: str, role: str = "agro_director", workspace: str = "agro") -> dict[str, str]:
    return {"X-Organization-Id": org, "X-Role": role, "X-Workspace-Id": workspace}


async def test_command_center_aggregated_empty_honest(client: TestClient):
    org = f"org-cc-read-{uuid.uuid4().hex[:8]}"
    body = await (await client.get(f"{OPS}/command-center", headers=_hdr(org))).json()
    assert body["ok"] is True
    assert body["organization_id"] == org
    assert body["workspace_id"] == "agro"
    assert body["timezone"]
    assert body["currency"]
    for key in ("kpis", "decisions", "today", "cash", "inventory", "logistics", "fields", "harvest", "risks", "data_quality"):
        assert key in body
    assert body["cash"]["empty_ru"] == "Остаток денежных средств не задан"
    assert body["logistics"]["empty_ru"] == "Нет активных перевозок"
    assert body["harvest"]["empty_ru"] == "Нет данных об урожае"
    blob = str(body).lower()
    assert "1240000" not in blob
    assert "4 280" not in blob


async def test_command_center_tenant_isolation(client: TestClient):
    a = f"org-a-{uuid.uuid4().hex[:8]}"
    b = f"org-b-{uuid.uuid4().hex[:8]}"
    created = await client.post(
        f"{OPS}/entities/deal",
        json={"title": "SECRET-A", "crop": "Пшеница", "status": "negotiation"},
        headers=_hdr(a),
    )
    assert created.status == 201
    other = await (await client.get(f"{OPS}/command-center", headers=_hdr(b))).json()
    assert other["ok"] is True
    assert other["organization_id"] == b
    assert "SECRET-A" not in str(other)


async def test_command_center_does_not_mix_currencies(client: TestClient):
    org = f"org-fx-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    due = (datetime.now(timezone.utc) - timedelta(days=3)).date().isoformat()
    await client.post(
        f"{OPS}/entities/invoice",
        json={"title": "AR-UAH", "amount": 1000, "currency": "UAH", "direction": "in", "status": "issued", "due_at": due},
        headers=h,
    )
    await client.post(
        f"{OPS}/entities/invoice",
        json={"title": "AR-USD", "amount": 50, "currency": "USD", "direction": "in", "status": "issued", "due_at": due},
        headers=h,
    )
    body = await (await client.get(f"{OPS}/command-center", headers=h)).json()
    cash = body["cash"]
    assert cash.get("fx", {}).get("available") is False
    currencies = {row["currency"] for row in (cash.get("receivables") or [])}
    assert currencies == {"UAH", "USD"} or cash.get("mixed") is True
    fin = await (await client.get(f"{OPS}/finance/summary", headers=h)).json()
    assert fin["receivables_total"] is None
    assert fin["mixed_currencies"] is True


async def test_command_center_rbac_scopes(client: TestClient):
    org = f"org-rbac-{uuid.uuid4().hex[:8]}"
    await client.post(
        f"{OPS}/entities/invoice",
        json={"title": "Bill", "amount": 10, "currency": "UAH", "direction": "out", "status": "issued"},
        headers=_hdr(org),
    )
    acc = await (await client.get(f"{OPS}/command-center", headers=_hdr(org, "agro_accountant"))).json()
    logi = await (await client.get(f"{OPS}/command-center", headers=_hdr(org, "agro_logistics"))).json()
    ware = await (await client.get(f"{OPS}/command-center", headers=_hdr(org, "agro_warehouse"))).json()
    agro = await (await client.get(f"{OPS}/command-center", headers=_hdr(org, "agro_agronomist"))).json()
    view = await (await client.get(f"{OPS}/command-center", headers=_hdr(org, "agro_viewer"))).json()
    assert acc["cash"].get("forbidden") is not True
    assert logi["cash"].get("forbidden") is True
    assert logi["logistics"].get("forbidden") is not True
    assert ware["inventory"].get("forbidden") is not True
    assert ware["logistics"].get("forbidden") is True
    assert agro["fields"] is not None
    assert agro["cash"].get("forbidden") is True
    assert view["ok"] is True
    denied = await client.post(f"{OPS}/entities/deal", json={"title": "x"}, headers=_hdr(org, "agro_viewer"))
    assert denied.status in {403, 400}


async def test_kpi_drilldown_filters(client: TestClient):
    org = f"org-drill-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    await client.post(
        f"{OPS}/entities/shipment",
        json={"title": "Run-1", "status": "in_transit", "crop": "Пшеница"},
        headers=h,
    )
    due = (datetime.now(timezone.utc) - timedelta(days=5)).date().isoformat()
    await client.post(
        f"{OPS}/entities/invoice",
        json={"title": "Overdue", "amount": 450000, "currency": "UAH", "direction": "in", "status": "issued", "due_at": due},
        headers=h,
    )
    body = await (await client.get(f"{OPS}/command-center", headers=h)).json()
    kpis = {k["id"]: k for k in body["kpis"]}
    assert kpis["shipments"]["view"] == "logistics"
    assert kpis["shipments"]["filter"] == "IN_TRANSIT"
    assert kpis["overdue"]["view"] == "accounting"
    assert kpis["overdue"]["filter"] == "overdue"
    assert kpis["overdue"]["value"] >= 1


async def test_exports_and_management_brief(client: TestClient):
    org = f"org-exp-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    for section in ("pnl", "receivables", "payables", "inventory", "crop-economics", "field-economics", "management-report"):
        res = await client.get(f"{OPS}/export/{section}", headers=h)
        assert res.status == 200, section
        text = await res.text()
        assert "id" in text or "metric" in text or "АГРО" in text or "crop" in text or "field" in text or "Нет данных" in text
    brief = await (await client.get(f"{OPS}/command-center/report", headers=h)).json()
    assert brief["ok"] is True
    assert "АГРО — УПРАВЛЕНЧЕСКАЯ СВОДКА" in brief["text"]
    html = await client.get(f"{OPS}/command-center/report?format=html", headers=h)
    assert html.status == 200
    assert "УПРАВЛЕНЧЕСКАЯ СВОДКА" in await html.text()
    activity = await (await client.get(f"{OPS}/entities/activity", headers=h)).json()
    items = activity.get("items") or []
    assert any(str(i.get("source") or "") in {"command_center", "user"} and "сводк" in str(i.get("summary") or "").lower() or i.get("entity_id") == "management_brief" for i in items)


async def test_health_still_agro_2_0(client: TestClient):
    body = await (await client.get(f"{OPS}/health")).json()
    assert body["sprint"] == "agro-2.0"
    assert body["command_center"] == "AGRO_2_0"
