"""AGRO 2.6 — fields / crops / sowing / works / machinery / harvest / economics."""

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


async def test_health_shows_2_6(client: TestClient):
    body = await (await client.get(f"{OPS}/health")).json()
    assert body["sprint"] == "agro-2.0"
    assert body["crm_version"] == "AGRO_2_1"
    assert body["ops_version"] == "AGRO_2_2"
    assert body["production_version"] == "AGRO_2_6"
    assert body["audit_version"] == "AGRO_2_5"
    assert body["catalogs"]["ownership_types"]
    assert body["catalogs"]["sowing_statuses"]
    assert body["catalogs"]["machine_types"]


async def test_flow_a_field_to_harvest(client: TestClient):
    org = f"org-a26-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    field = (
        await (
            await client.post(
                f"{OPS}/fields",
                json={
                    "name": "Поле Альфа",
                    "number": "A-1",
                    "area_ha": 50,
                    "region": "Одесская",
                    "district": "Белгород-Днестровский",
                    "locality": "Шабо",
                    "ownership_type": "lease",
                    "lease_start": "2025-01-01",
                    "lease_until": "2027-01-01",
                    "responsible": "Иванов",
                    "lat": 46.1,
                    "lng": 30.2,
                },
                headers=h,
            )
        ).json()
    )["item"]
    crop = (await (await client.post(f"{OPS}/agro-crops", json={"name": "Пшеница", "variety": "Одесская"}, headers=h)).json())["item"]
    assert crop["name"] == "Пшеница"
    sow = (
        await (
            await client.post(
                f"{OPS}/sowings",
                json={
                    "field_id": field["id"],
                    "crop": "Пшеница",
                    "variety": "Одесская",
                    "area": 50,
                    "seed_cost": 100000,
                    "fuel_cost": 20000,
                    "status": "plan",
                },
                headers=h,
            )
        ).json()
    )
    assert sow["ok"]
    assert sow["total_operation_cost"] == 120000
    assert sow["cost_per_hectare"] == 2400.0
    mach = (
        await (
            await client.post(
                f"{OPS}/machines",
                json={"name": "John Deere 8R", "type": "tractor", "plate": "BH1234", "status": "idle"},
                headers=h,
            )
        ).json()
    )["item"]
    work = (
        await (
            await client.post(
                f"{OPS}/works",
                json={
                    "field_id": field["id"],
                    "operation": "tillage",
                    "planned_date": "2026-03-01",
                    "machine_id": mach["id"],
                    "operator": "Петров",
                    "cost": 15000,
                },
                headers=h,
            )
        ).json()
    )
    assert work["ok"]
    st = await (
        await client.post(f"{OPS}/fields/works/{work['item']['id']}/status", json={"status": "in_progress"}, headers=h)
    ).json()
    assert st["ok"]
    done = await (
        await client.post(
            f"{OPS}/fields/works/{work['item']['id']}/status",
            json={"status": "done", "hours": 5},
            headers=h,
        )
    ).json()
    assert done["ok"]
    harv = (
        await (
            await client.post(
                f"{OPS}/harvests",
                json={
                    "field_id": field["id"],
                    "crop": "Пшеница",
                    "net_weight": 250,
                    "area_ha": 50,
                    "moisture": 14,
                    "price_per_t": 8000,
                },
                headers=h,
            )
        ).json()
    )
    assert harv["ok"]
    assert harv["yield_t_ha"] == 5.0
    assert harv["estimated_value"] == 2_000_000
    await client.post(
        f"{OPS}/fields/costs",
        json={
            "field_id": field["id"],
            "amount": 50000,
            "category": "fuel",
            "title": "Топливо тест",
            "source": "manual",
            "source_id": field["id"],
        },
        headers=h,
    )
    card = await (await client.get(f"{OPS}/fields/{field['id']}", headers=h)).json()
    assert card["ok"]
    assert card["item"]["ownership_type"] == "lease"
    assert card["economics"]["harvest_quantity"] == 250
    assert card["economics"]["total_costs"] is not None
    assert card["economics"]["total_costs"] >= 50000
    fmap = await (await client.get(f"{OPS}/fields/map", headers=h)).json()
    assert fmap["map_provider"]["id"] == "fallback_svg"
    feat = next(f for f in fmap["features"] if f["id"] == field["id"])
    assert feat["marker"]["lat"] == 46.1


async def test_flow_b_harvest_to_warehouse(client: TestClient):
    org = f"org-a26w-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    field = (await (await client.post(f"{OPS}/fields", json={"name": "Поле Б", "area_ha": 10}, headers=h)).json())["item"]
    await client.post(f"{OPS}/fields/{field['id']}/season", json={"crop": "Кукуруза", "year": 2026}, headers=h)
    harv = (
        await (
            await client.post(
                f"{OPS}/harvests",
                json={"field_id": field["id"], "actual_tonnes": 40, "area_ha": 10},
                headers=h,
            )
        ).json()
    )["item"]
    wh_item = (await (await client.post(f"{OPS}/entities/warehouse", json={"name": "Элеватор 26"}, headers=h)).json())["item"]
    wh = await (
        await client.post(
            f"{OPS}/harvest/to-warehouse",
            json={"harvest_id": harv["id"], "warehouse_id": wh_item["id"], "plate": "AA9999BB"},
            headers=h,
        )
    ).json()
    assert wh["ok"]
    listed = await (await client.get(f"{OPS}/harvests", headers=h)).json()
    row = next(i for i in listed["items"] if i["id"] == harv["id"])
    assert row["linked_warehouse"] is True


async def test_kpis_26_from_persisted(client: TestClient):
    org = f"org-a26k-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    await client.post(f"{OPS}/fields", json={"name": "F1", "area_ha": 20}, headers=h)
    await client.post(f"{OPS}/machines", json={"name": "T1", "type": "tractor", "status": "working"}, headers=h)
    kpis = await (await client.get(f"{OPS}/production/kpis-26", headers=h)).json()
    assert kpis["ok"]
    by_id = {m["id"]: m["value"] for m in kpis["metrics"]}
    assert by_id["fields_total"] == 1
    assert by_id["hectares_total"] == 20
    assert by_id["machinery_active"] == 1


async def test_list_modules_search(client: TestClient):
    org = f"org-a26s-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    await client.post(f"{OPS}/agro-crops", json={"name": "Соя", "variety": "Х"}, headers=h)
    crops = await (await client.get(f"{OPS}/agro-crops?q=соя", headers=h)).json()
    assert crops["total"] >= 1
    works = await (await client.get(f"{OPS}/works", headers=h)).json()
    assert works["ok"]
    machines = await (await client.get(f"{OPS}/machines", headers=h)).json()
    assert machines["ok"]
