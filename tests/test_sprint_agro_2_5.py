"""AGRO 2.5 — navigation journey, demo exclusion, terminology/audit markers."""

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


async def test_health_audit_version_2_5(client: TestClient):
    body = await (await client.get(f"{OPS}/health")).json()
    assert body["sprint"] == "agro-2.0"
    assert body["command_center"] == "AGRO_2_0"
    assert body["audit_version"] == "AGRO_2_5"


async def test_demo_excluded_from_command_center_and_finance(client: TestClient):
    org = f"org-demo-25-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    live = await client.post(
        f"{OPS}/entities/deal",
        json={"title": "Живая сделка", "crop": "Пшеница", "status": "negotiation", "quantity": 10, "price": 100},
        headers=h,
    )
    assert live.status == 201
    demo = await client.post(
        f"{OPS}/entities/deal",
        json={"title": "[DEMO] Тестовая", "crop": "Пшеница", "status": "negotiation", "quantity": 99, "price": 999, "is_demo": True},
        headers=h,
    )
    assert demo.status == 201
    due = (datetime.now(timezone.utc) - timedelta(days=2)).date().isoformat()
    await client.post(
        f"{OPS}/entities/invoice",
        json={"title": "[DEMO] счёт", "amount": 999999, "currency": "UAH", "direction": "in", "status": "issued", "due_at": due, "is_demo": True},
        headers=h,
    )
    await client.post(
        f"{OPS}/entities/invoice",
        json={"title": "Живой счёт", "amount": 1500, "currency": "UAH", "direction": "in", "status": "issued", "due_at": due},
        headers=h,
    )
    cc = await (await client.get(f"{OPS}/command-center", headers=h)).json()
    blob = str(cc)
    assert "[DEMO]" not in blob or "DEMO" not in str(cc.get("kpis"))
    assert "999999" not in blob
    deals_items = ((cc.get("command_center") or {}).get("deals") or {}).get("items") or []
    assert all(not d.get("is_demo") for d in deals_items)
    assert all("[DEMO]" not in str(d.get("title") or "") for d in deals_items)
    fin = await (await client.get(f"{OPS}/finance/summary", headers=h)).json()
    assert fin["ok"] is True
    assert fin["overdue_total"] == 1500
    assert 999999 not in [r.get("amount") for r in (fin.get("overdue") or [])]


async def test_tenant_isolation_command_center_2_5(client: TestClient):
    a = f"org-a25-{uuid.uuid4().hex[:8]}"
    b = f"org-b25-{uuid.uuid4().hex[:8]}"
    await client.post(f"{OPS}/entities/deal", json={"title": "SECRET-A25", "status": "negotiation"}, headers=_hdr(a))
    other = await (await client.get(f"{OPS}/command-center", headers=_hdr(b))).json()
    assert "SECRET-A25" not in str(other)


async def test_search_inventory_lot_label_ru(client: TestClient):
    org = f"org-search-25-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    wh = await client.post(f"{OPS}/entities/warehouse", json={"name": "Элеватор Юг"}, headers=h)
    assert wh.status == 201
    wid = (await wh.json())["item"]["id"]
    lot = await client.post(
        f"{OPS}/entities/inventory_lot",
        json={"lot_number": "LOT-SEARCH-25", "warehouse_id": wid, "commodity": "Пшеница", "quantity": 12},
        headers=h,
    )
    assert lot.status == 201
    res = await (await client.get(f"{OPS}/search?q=LOT-SEARCH-25", headers=h)).json()
    groups = {g["id"]: g for g in res.get("groups") or []}
    assert "inventory_lot" in groups
    assert groups["inventory_lot"]["label_ru"] == "Складская партия"


async def test_viewer_cannot_mutate(client: TestClient):
    org = f"org-view-25-{uuid.uuid4().hex[:8]}"
    denied = await client.post(f"{OPS}/entities/deal", json={"title": "x"}, headers=_hdr(org, "agro_viewer"))
    assert denied.status in {403, 400}
