"""AGRO Operations 1.1 — providers, logistics, markets, warehouses."""

from __future__ import annotations

import json
import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.agro_enterprise.api.register import register_agro_enterprise_routes
from services.agro_ops import get_agro_ops_service, reset_agro_ops_for_tests
from services.agro_ops.providers import SimpleFetchResult

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


async def _fake_fetch(url: str, headers=None) -> SimpleFetchResult:
    if "data.gov.ua" in url:
        return SimpleFetchResult(
            status=200,
            text=json.dumps(
                {
                    "success": True,
                    "result": {
                        "results": [
                            {"id": "pkg-1", "title": "Митна статистика", "metadata_modified": "2026-08-01T00:00:00"}
                        ]
                    },
                }
            ),
        )
    if "cornell" in url:
        return SimpleFetchResult(
            status=200,
            text=json.dumps({"id": "wasde", "title": "WASDE", "date_created": "2026-08-12", "file_sets": []}),
        )
    if "faostat" in url:
        return SimpleFetchResult(status=200, text=json.dumps({"data": [{"domain_code": "PP", "domain_name": "Producer Prices"}]}))
    if "worldbank" in url:
        return SimpleFetchResult(status=200, text=json.dumps([{}, [{"id": "2", "name": "World Development Indicators"}]]))
    if url.endswith("/") or "meteo" in url or "agridata" in url or "minagro" in url or "uspa" in url or "amis" in url or "eurostat" in url:
        return SimpleFetchResult(status=200, text="<!doctype html><html><body>official</body></html>")
    return SimpleFetchResult(unavailable=True, error="no mock")


async def test_health_sprint_1_1(client: TestClient):
    body = await (await client.get(f"{OPS}/health")).json()
    assert body["sprint"] == "agro-2.0"
    assert "client_secret" not in str(body).lower()


async def test_unprobed_providers_stay_not_configured(client: TestClient):
    org = f"org-a11-{uuid.uuid4().hex[:8]}"
    items = {i["id"]: i for i in (await (await client.get(f"{OPS}/providers", headers=_hdr(org))).json())["items"]}
    assert items["usda_wasde"]["status"] == "NOT_CONFIGURED"
    assert items["manual_import"]["status"] == "LIVE"
    assert items["weather_provider_secondary"]["connection_status"] in {"NOT_CONFIGURED", "NEEDS_KEY"}


async def test_provider_probe_dedupe_and_honest_status(client: TestClient):
    org = f"org-a11p-{uuid.uuid4().hex[:8]}"
    svc = get_agro_ops_service()
    svc.set_provider_fetch(_fake_fetch)
    first = await (await client.post(f"{OPS}/providers/ua_customs_open_data/probe", json={}, headers=_hdr(org))).json()
    assert first["ok"]
    assert first["item"]["probe_result"] == "PARTIAL"
    assert first["observations"]
    second = await (await client.post(f"{OPS}/providers/ua_customs_open_data/probe", json={}, headers=_hdr(org))).json()
    assert second["ok"]
    obs = await (await client.get(f"{OPS}/providers/observations?provider_id=ua_customs_open_data", headers=_hdr(org))).json()
    trade = [i for i in obs["items"] if i.get("record_kind") == "trade_observation"]
    assert len(trade) == 1
    blocked = await client.post(f"{OPS}/providers/usda_wasde/probe", json={}, headers=_hdr(org, "agro_observer"))
    assert (await blocked.json()).get("error") == "forbidden"


async def test_logistics_crud_and_trip_economics(client: TestClient):
    org = f"org-a11l-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    cp = (await (await client.post(f"{OPS}/entities/counterparty", json={"name": "ООО Тест Агро", "types": ["supplier", "carrier"]}, headers=h)).json())["item"]
    carrier = (await (await client.post(f"{OPS}/entities/carrier", json={"name": "ООО Тест Агро", "counterparty_id": cp["id"], "carrier_type": "carrier"}, headers=h)).json())["item"]
    vehicle = (await (await client.post(f"{OPS}/entities/vehicle", json={"plate": "AA0001AA", "carrier_id": carrier["id"], "brand": "МАЗ"}, headers=h)).json())["item"]
    assert vehicle["plate"] == "AA0001AA"
    trailer = await client.post(f"{OPS}/entities/trailer", json={"plate": "AA0002XX", "carrier_id": carrier["id"]}, headers=h)
    assert trailer.status == 201
    driver = (await (await client.post(f"{OPS}/entities/driver", json={"full_name": "Иван Водитель", "carrier_id": carrier["id"], "license_number": "АВС123"}, headers=h)).json())["item"]
    deal = (await (await client.post(f"{OPS}/entities/deal", json={"title": "Пшеница 100т", "crop": "Пшеница", "quantity": 100, "counterparty_id": cp["id"]}, headers=h)).json())["item"]
    trip = (await (await client.post(
        f"{OPS}/entities/trip",
        json={
            "title": "Рейс-1",
            "carrier_id": carrier["id"],
            "vehicle_id": vehicle["id"],
            "driver_id": driver["id"],
            "deal_id": deal["id"],
            "weight_planned": 100,
            "rate": 20000,
            "fuel_cost": 3000,
            "distance": 400,
            "crop": "Пшеница",
        },
        headers=h,
    )).json())["item"]
    assert trip["total_logistics_cost"] == 23000
    assert trip["cost_per_tonne"] == 230
    dash = await (await client.get(f"{OPS}/logistics/dashboard", headers=h)).json()
    assert dash["cards"]["active_trips"] >= 1
    other = await (await client.get(f"{OPS}/entities/vehicle", headers=_hdr(f"org-other-{uuid.uuid4().hex[:6]}"))).json()
    assert all(i.get("plate") != "AA0001AA" for i in other["items"])


async def test_sensitive_driver_docs_rbac(client: TestClient):
    org = f"org-a11s-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    driver = (await (await client.post(f"{OPS}/entities/driver", json={"full_name": "Секрет"}, headers=h)).json())["item"]
    import base64

    uploaded = await client.post(
        f"{OPS}/files",
        json={
            "filename": "license.pdf",
            "content_base64": base64.b64encode(TINY_PDF).decode(),
            "entity_type": "driver",
            "entity_id": driver["id"],
            "doc_type": "driver_license",
        },
        headers=h,
    )
    assert uploaded.status in {200, 201}
    file_id = (await uploaded.json())["item"]["id"]
    hidden = await (await client.get(f"{OPS}/files", headers=_hdr(org, "agro_manager"))).json()
    assert all(i.get("id") != file_id for i in hidden["items"])
    forbidden = await client.get(f"{OPS}/files/{file_id}/content", headers=_hdr(org, "agro_manager"))
    assert forbidden.status == 403
    visible = await (await client.get(f"{OPS}/files", headers=h)).json()
    assert any(i.get("id") == file_id for i in visible["items"])


async def test_manual_price_history_never_overwrites(client: TestClient):
    org = f"org-a11m-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    market = (await (await client.post(f"{OPS}/entities/market", json={"name": "Одесса — ручной рынок", "market_type": "manual"}, headers=h)).json())["item"]
    p1 = await client.post(f"{OPS}/entities/market_price", json={"market_id": market["id"], "commodity": "Пшеница", "price": 8000, "valid_from": "2026-08-01"}, headers=h)
    p2 = await client.post(f"{OPS}/entities/market_price", json={"market_id": market["id"], "commodity": "Пшеница", "price": 8200, "valid_from": "2026-08-10"}, headers=h)
    assert p1.status == 201 and p2.status == 201
    hist = await (await client.get(f"{OPS}/markets/history?crop=Пшеница&span=1Y", headers=h)).json()
    assert len(hist["points"]) == 2
    dash = await (await client.get(f"{OPS}/markets/dashboard?crop=Пшеница", headers=h)).json()
    assert dash["current"][0]["price"] == 8200
    assert dash["current"][0]["change"] == 200
    landed = await (await client.post(f"{OPS}/markets/landed-cost", json={"purchase_price": 8000, "sale_price": 9000, "transport": 200, "quantity": 100}, headers=h)).json()
    assert landed["ok"]
    assert landed["item"]["delivered_cost"] == 800200


async def test_warehouse_receipt_issue_and_negative_guard(client: TestClient):
    org = f"org-a11w-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    wh = (await (await client.post(f"{OPS}/entities/warehouse", json={"name": "Одесский склад", "capacity_total": 1000}, headers=h)).json())["item"]
    rec = await (await client.post(
        f"{OPS}/warehouses/operations",
        json={"type": "RECEIPT", "warehouse_id": wh["id"], "commodity": "Пшеница", "quantity": 100, "purchase_price": 7000},
        headers=h,
    )).json()
    assert rec["ok"]
    lot_id = rec["item"]["lot_id"]
    lots = await (await client.get(f"{OPS}/entities/inventory_lot", headers=h)).json()
    assert lots["items"][0]["quantity"] == 100
    iss = await (await client.post(
        f"{OPS}/warehouses/operations",
        json={"type": "ISSUE", "warehouse_id": wh["id"], "lot_id": lot_id, "quantity": 20, "commodity": "Пшеница"},
        headers=h,
    )).json()
    assert iss["ok"]
    lots = await (await client.get(f"{OPS}/entities/inventory_lot", headers=h)).json()
    assert lots["items"][0]["quantity"] == 80
    denied = await (await client.post(
        f"{OPS}/warehouses/operations",
        json={"type": "ISSUE", "warehouse_id": wh["id"], "lot_id": lot_id, "quantity": 500},
        headers=h,
    )).json()
    assert denied.get("error") == "validation"
    dash = await (await client.get(f"{OPS}/warehouses/dashboard", headers=h)).json()
    assert dash["cards"]["occupied"] == 80
    assert dash["cards"]["capacity_total"] == 1000


async def test_scenario_links_survive_and_rbac(client: TestClient):
    org = f"org-a11x-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    cp = (await (await client.post(f"{OPS}/entities/counterparty", json={"name": "ООО Тест Агро", "types": ["supplier", "carrier"]}, headers=h)).json())["item"]
    deal = (await (await client.post(f"{OPS}/entities/deal", json={"title": "Пшеница 100", "crop": "Пшеница", "quantity": 100, "counterparty_id": cp["id"]}, headers=h)).json())["item"]
    trip = (await (await client.post(f"{OPS}/entities/trip", json={"title": "R1", "deal_id": deal["id"], "counterparty_id": cp["id"], "weight_planned": 100, "rate": 1000}, headers=h)).json())["item"]
    rel = await (await client.get(f"{OPS}/entities/deal/{deal['id']}/related", headers=h)).json()
    assert any(t["id"] == trip["id"] for t in rel["related"]["trips"])
    acc = await client.post(f"{OPS}/entities/vehicle", json={"plate": "XX0000XX"}, headers=_hdr(org, "agro_accountant"))
    assert (await acc.json()).get("error") == "forbidden"
