"""AGRO 2.3 — field production. Extends agro-ops. Does not start 2.4."""

from __future__ import annotations

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
    return {"X-Organization-Id": org, "X-Role": role, "X-Workspace-Id": "agro"}


async def test_health_keeps_prior_sprints_and_adds_2_3(client: TestClient):
    body = await (await client.get(f"{OPS}/health")).json()
    assert body["sprint"] == "agro-2.0"
    assert body["ux_version"] == "AGRO_2_0"
    assert body["command_center"] == "AGRO_2_0"
    assert body["crm_version"] == "AGRO_2_1"
    assert body["ops_version"] == "AGRO_2_2"
    assert body["production_version"] == "AGRO_2_6"
    cats = body["catalogs"]
    assert cats["production_version"] == "AGRO_2_6"
    assert any(r["id"] == "agro_agronomist" for r in body["roles"])
    assert any(r["id"] == "agro_mechanic" for r in body["roles"])
    assert "RECEIPT" in cats["material_moves"]


async def test_numeric_acceptance_seed_yield_cost(client: TestClient):
    org = f"org-a23-n-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    field = (await (await client.post(f"{OPS}/fields", json={"name": "Поле 100", "area_ha": 100}, headers=h)).json())["item"]
    await client.post(f"{OPS}/fields/{field['id']}/season", json={"crop": "Пшеница", "year": 2026, "planned_seed_rate": 200}, headers=h)
    mat = (await (await client.post(f"{OPS}/materials", json={"name": "Семена пшеницы", "category": "seed", "unit": "кг"}, headers=h)).json())["item"]
    rec = await client.post(f"{OPS}/materials/move", json={"material_id": mat["id"], "movement_type": "RECEIPT", "quantity": 20000}, headers=h)
    assert rec.status == 201
    iss = await client.post(
        f"{OPS}/materials/issue",
        json={"material_id": mat["id"], "quantity": 19800, "field_id": field["id"]},
        headers=h,
    )
    assert iss.status == 201
    harv = await (
        await client.post(
            f"{OPS}/fields/{field['id']}/harvest",
            json={"actual_tonnes": 620, "area_harvested": 100},
            headers=h,
        )
    ).json()
    assert harv["yield_t_ha"] == 6.2
    cost = await client.post(
        f"{OPS}/fields/costs",
        json={"field_id": field["id"], "amount": 3_100_000, "category": "other", "source": "ledger", "source_id": harv["item"]["id"]},
        headers=h,
    )
    assert cost.status == 201
    card = await (await client.get(f"{OPS}/fields/{field['id']}", headers=h)).json()
    item = card["item"]
    assert item["seed_rate_kg_ha"] == 198
    assert item["yield_t_ha"] == 6.2
    assert item["cost_ha"] == 31000
    assert item["cost_t"] == 5000


async def test_material_ledger_no_direct_overwrite(client: TestClient):
    org = f"org-a23-m-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    mat = (await (await client.post(f"{OPS}/materials", json={"name": "Дап", "category": "fertilizer"}, headers=h)).json())["item"]
    assert mat["quantity"] == 0
    await client.post(f"{OPS}/materials/move", json={"material_id": mat["id"], "movement_type": "RECEIPT", "quantity": 50}, headers=h)
    bad = await client.post(f"{OPS}/materials/issue", json={"material_id": mat["id"], "quantity": 80, "field_id": "x"}, headers=h)
    assert bad.status == 400
    ok = await client.post(f"{OPS}/materials/move", json={"material_id": mat["id"], "movement_type": "ISSUE", "quantity": 20}, headers=h)
    assert ok.status == 201
    listed = await (await client.get(f"{OPS}/entities/material", headers=h)).json()
    row = next(i for i in listed["items"] if i["id"] == mat["id"])
    assert row["quantity"] == 30


async def test_harvest_reuses_2_2_warehouse(client: TestClient):
    org = f"org-a23-h-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    field = (await (await client.post(f"{OPS}/fields", json={"name": "Поле 17", "area_ha": 124}, headers=h)).json())["item"]
    await client.post(f"{OPS}/fields/{field['id']}/season", json={"crop": "Пшеница", "year": 2026}, headers=h)
    harv = (await (await client.post(f"{OPS}/fields/{field['id']}/harvest", json={"actual_tonnes": 40, "area_harvested": 124}, headers=h)).json())["item"]
    wh = (await (await client.post(f"{OPS}/entities/warehouse", json={"name": "Элеватор"}, headers=h)).json())["item"]
    linked = await (
        await client.post(
            f"{OPS}/harvest/to-warehouse",
            json={"harvest_id": harv["id"], "warehouse_id": wh["id"], "plate": "AA1234BB"},
            headers=h,
        )
    ).json()
    assert linked["ok"] is True
    assert linked["operation_id"]
    lot_id = linked["receipt"]["item"]["id"]
    stock = await (await client.get(f"{OPS}/operations/stock", headers=h)).json()
    lots = stock.get("lots") or []
    found = next((x for x in lots if x.get("id") == lot_id), None)
    assert found is not None
    card = await (await client.get(f"{OPS}/fields/{field['id']}", headers=h)).json()
    labels = [s["label"] for s in card["trace_forward"]]
    assert "harvest" in labels
    assert "lot" in labels


async def test_rbac_and_tenant_isolation(client: TestClient):
    org_a = f"org-a23-a-{uuid.uuid4().hex[:8]}"
    org_b = f"org-a23-b-{uuid.uuid4().hex[:8]}"
    field = (await (await client.post(f"{OPS}/fields", json={"name": "A", "area_ha": 10}, headers=_hdr(org_a))).json())["item"]
    other = await (await client.get(f"{OPS}/fields/{field['id']}", headers=_hdr(org_b))).json()
    assert other.get("error") == "not_found"
    viewer = await client.post(f"{OPS}/fields", json={"name": "V", "area_ha": 5}, headers=_hdr(org_a, "agro_viewer"))
    assert viewer.status == 403
    mech = await client.post(f"{OPS}/fields", json={"name": "M", "area_ha": 5}, headers=_hdr(org_a, "agro_mechanic"))
    assert mech.status == 403
    tractor = await client.post(f"{OPS}/machines", json={"plate": "TR-1", "kind": "tractor"}, headers=_hdr(org_a, "agro_mechanic"))
    assert tractor.status == 201
    agr = await client.post(f"{OPS}/fields", json={"name": "Agr", "area_ha": 8}, headers=_hdr(org_a, "agro_agronomist"))
    assert agr.status == 201


async def test_missing_yield_is_empty_not_invented(client: TestClient):
    org = f"org-a23-e-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    field = (await (await client.post(f"{OPS}/fields", json={"name": "Пустое", "area_ha": 50}, headers=h)).json())["item"]
    card = await (await client.get(f"{OPS}/fields/{field['id']}", headers=h)).json()
    assert card["item"]["yield_t_ha"] is None
    assert card["item"]["cost_ha"] is None
    assert card["item"]["cost_t"] is None


async def test_production_demo_is_labelled(client: TestClient):
    org = f"org-a23-d-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    res = await (await client.post(f"{OPS}/production/bootstrap", headers=h)).json()
    assert res["ok"] is True
    assert "[DEMO]" in (res["item"]["name"] or "")
    listed = await (await client.get(f"{OPS}/fields", headers=h)).json()
    assert listed["items"][0]["is_demo"] is True


async def test_work_calendar_and_issue_task(client: TestClient):
    org = f"org-a23-c-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    field = (await (await client.post(f"{OPS}/fields", json={"name": "Поле 17", "area_ha": 124}, headers=h)).json())["item"]
    work = await client.post(
        f"{OPS}/fields/{field['id']}/work",
        json={"work_type": "sowing", "planned_at": "2026-03-20T08:00:00"},
        headers=h,
    )
    assert work.status == 201
    cal = await (await client.get(f"{OPS}/entities/calendar", headers=h)).json()
    assert any("Посев" in str(e.get("title") or "") or e.get("field_id") == field["id"] for e in cal["items"])
    iss = await client.post(
        f"{OPS}/fields/{field['id']}/issue",
        json={"issue_type": "weeds", "description": "Амброзия", "create_task": True},
        headers=h,
    )
    assert iss.status == 201
    tasks = await (await client.get(f"{OPS}/entities/task", headers=h)).json()
    assert any(t.get("entity_type") == "field_issue" or t.get("field_id") == field["id"] for t in tasks["items"])
    await client.post(f"{OPS}/maintenance", json={"machine_id": "m1", "due_date": "2020-01-01", "maintenance_type": "service"}, headers=h)
    alerts = await (await client.post(f"{OPS}/production/alerts", headers=h)).json()
    assert alerts["created"] >= 1
    notes = await (await client.get(f"{OPS}/entities/notification", headers=h)).json()
    assert notes["items"]
