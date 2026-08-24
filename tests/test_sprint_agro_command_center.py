"""AGRO 2.0 Operational Command Center — dashboard aggregation, search, honesty."""

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


def _hdr(org: str, role: str = "agro_director") -> dict[str, str]:
    return {"X-Organization-Id": org, "X-Role": role}


async def test_health_keeps_agro_2_0_and_command_center(client: TestClient):
    body = await (await client.get(f"{OPS}/health")).json()
    assert body["sprint"] == "agro-2.0"
    assert body["ux_version"] == "AGRO_2_0"
    assert body["command_center"] == "AGRO_2_0"
    assert any(r["id"] == "agro_logistics" for r in body["roles"])
    assert any(r["id"] == "agro_warehouse" for r in body["roles"])


async def test_empty_command_center_is_honest(client: TestClient):
    org = f"org-cc-empty-{uuid.uuid4().hex[:8]}"
    dash = await (await client.get(f"{OPS}/dashboard", headers=_hdr(org))).json()
    assert dash["ok"] is True
    assert "cards" in dash
    cc = dash["command_center"]
    assert cc["version"] == "AGRO_2_0"
    by_id = {c["id"]: c for c in cc["summary"]}
    assert by_id["deals"]["value"] == 0
    assert by_id["shipments"]["value"] == 0
    assert by_id["critical"]["value"] == 0
    assert cc["today"] == []
    assert cc["deals"]["items"] == []
    assert cc["shipments"]["items"] == []
    assert cc["markets"] == []
    assert all(r.get("missing") for r in cc["weather"]["regions"])
    assert all(c.get("missing") for c in cc["intel"])
    fake = str(dash).lower()
    assert "1240000" not in fake
    assert "4 280" not in fake


async def test_command_center_uses_real_records(client: TestClient):
    org = f"org-cc-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    cp = await client.post(f"{OPS}/entities/counterparty", json={"name": "ТОВ Зерно", "edrpou": "12345678", "types": ["buyer"]}, headers=h)
    assert cp.status == 201
    cid = (await cp.json())["item"]["id"]
    deal = await client.post(
        f"{OPS}/entities/deal",
        json={"title": "Пшеница спот", "counterparty_id": cid, "crop": "Пшеница", "quantity": 100, "price": 8000, "status": "negotiation"},
        headers=h,
    )
    assert deal.status == 201
    did = (await deal.json())["item"]["id"]
    past = (datetime.now(timezone.utc) - timedelta(days=2)).date().isoformat()
    ship = await client.post(
        f"{OPS}/entities/shipment",
        json={"title": "Поставка-1", "deal_id": did, "counterparty_id": cid, "crop": "Пшеница", "quantity": 40, "status": "in_transit", "deadline_at": past},
        headers=h,
    )
    assert ship.status == 201
    await client.post(
        f"{OPS}/entities/task",
        json={"title": "Позвонить клиенту", "due_at": past, "deal_id": did, "status": "open"},
        headers=h,
    )
    await client.post(
        f"{OPS}/entities/warehouse",
        json={"name": "Элеватор Юг", "city": "Одесса", "capacity_total": 5000},
        headers=h,
    )
    await client.post(
        f"{OPS}/entities/market_price",
        json={"commodity": "Пшеница", "price": 8100, "currency": "UAH", "unit": "т", "source_type": "MANUAL"},
        headers=h,
    )
    dash = await (await client.get(f"{OPS}/dashboard", headers=h)).json()
    cc = dash["command_center"]
    by_id = {c["id"]: c for c in cc["summary"]}
    assert by_id["deals"]["value"] >= 1
    assert by_id["shipments"]["value"] >= 1
    assert any(e["title"] == "Поставка задерживается" for e in cc["today"])
    assert any(e["title"] == "Задача просрочена" for e in cc["today"])
    pipe = {p["id"]: p for p in cc["deals"]["pipeline"]}
    assert pipe["negotiation"]["count"] >= 1
    assert pipe["negotiation"]["value"] == 800000.0
    wheat = next((m for m in cc["markets"] if m["crop"] == "Пшеница"), None)
    assert wheat is not None
    assert wheat["price"] == 8100
    assert wheat["source_label_ru"] == "Ручная"
    assert wheat["manual"] is True
    assert cc["warehouses"]["items"]
    assert cc["warehouses"]["items"][0]["name"] == "Элеватор Юг"


async def test_accountant_masks_margins_and_manager_can_open(client: TestClient):
    org = f"org-cc-rbac-{uuid.uuid4().hex[:8]}"
    h = _hdr(org, "agro_director")
    await client.post(
        f"{OPS}/entities/deal",
        json={"title": "Кукуруза", "crop": "Кукуруза", "quantity": 10, "price": 5000, "status": "approved"},
        headers=h,
    )
    acc = await (await client.get(f"{OPS}/dashboard", headers=_hdr(org, "agro_accountant"))).json()
    assert acc["command_center"]["can_finance"] is True
    assert acc["command_center"]["can_create"] is False
    mgr = await (await client.get(f"{OPS}/dashboard", headers=_hdr(org, "agro_manager"))).json()
    assert mgr["command_center"]["can_create"] is True
    assert mgr["command_center"]["can_finance"] is False
    pay = next(c for c in mgr["command_center"]["summary"] if c["id"] == "payables")
    assert pay["masked"] is True
    logi = await (await client.get(f"{OPS}/dashboard", headers=_hdr(org, "agro_logistics"))).json()
    assert "shipments" in logi["command_center"]["blocks"][2] or logi["command_center"]["blocks"][0] == "summary"


async def test_global_search_edrpou_and_deal(client: TestClient):
    org = f"org-cc-search-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    await client.post(
        f"{OPS}/entities/counterparty",
        json={"name": "Агротрейд", "edrpou": "99887766", "phone": "+380501112233", "types": ["trader"]},
        headers=h,
    )
    await client.post(f"{OPS}/entities/deal", json={"title": "Сделка-77", "crop": "Ячмень"}, headers=h)
    found = await (await client.get(f"{OPS}/search?q=99887766", headers=h)).json()
    assert found["ok"] is True
    groups = {g["id"]: g for g in found["groups"]}
    assert "counterparty" in groups
    deal = await (await client.get(f"{OPS}/search?q=Сделка-77", headers=h)).json()
    assert any(g["id"] == "deal" for g in deal["groups"])
    empty = await (await client.get(f"{OPS}/search?q=", headers=h)).json()
    assert empty["groups"] == []


async def test_related_bundle_includes_payments_and_ops(client: TestClient):
    org = f"org-cc-rel-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    cp = (await (await client.post(f"{OPS}/entities/counterparty", json={"name": "Ферма А", "types": ["farm"], "notes": "Ключевой поставщик"}, headers=h)).json())["item"]
    deal = (await (await client.post(f"{OPS}/entities/deal", json={"title": "Рапс", "counterparty_id": cp["id"], "crop": "Рапс"}, headers=h)).json())["item"]
    await client.post(f"{OPS}/entities/payment", json={"title": "Оплата рапса", "amount": 100, "counterparty_id": cp["id"], "deal_id": deal["id"]}, headers=h)
    rel = await (await client.get(f"{OPS}/entities/counterparty/{cp['id']}/related", headers=h)).json()
    assert rel["related"]["payments"]
    assert rel["related"]["deals"]
    assert rel["related"]["notes"]
