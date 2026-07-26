"""Tests — Agriculture Pilot Execution & Trade Validation (Sprint 31.1)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.agro_marketplace import agro_marketplace
from applications.agro_marketplace.api.register import register_agro_marketplace_routes
from applications.agro_enterprise import agro_enterprise
from applications.agro_enterprise.api.register import register_agro_enterprise_routes


ROOT = Path(__file__).resolve().parents[1]
AGRO = "/api/agro/v1"
SC = "/api/agro-supply-chain/v1"

DOCS = [
    "AGRICULTURE_PILOT_EXECUTION_31_1.md",
    "AGRICULTURE_INTEGRATION_31_1.md",
    "TRADE_WORKFLOW_31_1.md",
    "LOGISTICS_GUIDE_31_1.md",
    "ECOSYSTEM_REUSE_MATRIX_31_1.md",
    "API_STATUS_31_1.md",
    "PRODUCTION_STATUS_31_1.md",
    "RELEASE_NOTES_31_1.md",
    "SPRINT_REPORT_31_1.md",
]


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_agro_marketplace_routes(application)
    register_agro_enterprise_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    platform_builder.reset()
    agro_marketplace.reset()
    agro_enterprise.reset()
    yield
    platform_builder.reset()
    agro_marketplace.reset()
    agro_enterprise.reset()


def test_agriculture_docs_exist():
    docs = ROOT / "docs"
    for name in DOCS:
        path = docs / name
        assert path.exists(), name
        assert "31.1" in path.read_text()


def test_platform_agriculture_version():
    health = platform_builder.health()
    assert health["application_version"] == "1.42.0"
    assert health["sprint"] == "32.2"
    assert health["release_status"] == "First External Pilot Execution & Product Feedback Loop"


@pytest.mark.asyncio
async def test_agriculture_trade_and_logistics_api(client):
    farmer = await client.post(
        f"{AGRO}/farmers",
        json={"name": "Pilot Farmer", "email": "agro31@demo.corp", "country": "KE", "region": "Rift"},
    )
    assert farmer.status == 201
    farmer_body = await farmer.json()
    farmer_id = farmer_body["farmer_id"]

    farm = await client.post(
        f"{AGRO}/farms",
        json={"farmer_id": farmer_id, "name": "Pilot Farm", "size_hectares": 25, "location": "Nakuru"},
    )
    assert farm.status == 201
    farm_body = await farm.json()

    field = await client.post(
        f"{AGRO}/fields",
        json={
            "farm_id": farm_body["farm_id"],
            "name": "North Field",
            "crop_type": "wheat",
            "area_hectares": 8,
            "soil_type": "loam",
        },
    )
    assert field.status == 201

    product = await client.post(
        f"{AGRO}/products",
        json={"name": "Pilot Wheat", "farmer_id": farmer_id, "price": 210, "quantity": 50, "crop_id": "wheat"},
    )
    assert product.status == 201
    product_body = await product.json()

    season = await client.post(
        f"{AGRO}/harvest/seasons",
        json={"name": "Main Season", "year": 2026, "region": "KE"},
    )
    assert season.status in (200, 201)
    season_body = await season.json()

    harvest = await client.post(
        f"{AGRO}/harvest/records",
        json={
            "crop_id": "wheat",
            "season_id": season_body.get("season_id"),
            "region": "KE",
            "quantity": 40,
            "moisture_pct": 13,
            "farm_id": farm_body["farm_id"],
            "farmer_id": farmer_id,
        },
    )
    assert harvest.status in (200, 201)
    harvest_body = await harvest.json()

    wh = await client.post(
        f"{AGRO}/warehouse/warehouses",
        json={"name": "Pilot Silo", "region": "KE", "capacity_tons": 250, "owner_id": farmer_id},
    )
    assert wh.status in (200, 201)
    wh_body = await wh.json()

    inv = await client.post(
        f"{AGRO}/inventory/incoming",
        json={
            "product_id": product_body["product_id"],
            "warehouse_id": wh_body["warehouse_id"],
            "quantity": 40,
        },
    )
    assert inv.status in (200, 201)

    buyer = await client.post(
        f"{AGRO}/crm/buyers",
        json={"name": "Export Mill", "email": "mill@demo.corp", "preferred_crops": ["wheat"], "budget_max": 200000},
    )
    assert buyer.status in (200, 201)
    buyer_body = await buyer.json()

    offer = await client.post(
        f"{AGRO}/marketplace/offers",
        json={"seller_id": farmer_id, "crop_id": "wheat", "quantity": 30, "price": 210, "region": "KE"},
    )
    assert offer.status in (200, 201)
    offer_body = await offer.json()

    request = await client.post(
        f"{AGRO}/marketplace/requests",
        json={
            "buyer_id": buyer_body["buyer_id"],
            "crop_id": "wheat",
            "quantity": 25,
            "max_price": 220,
            "region": "KE",
        },
    )
    assert request.status in (200, 201)
    request_body = await request.json()

    match = await client.post(
        f"{AGRO}/marketplace/match",
        json={"offer_id": offer_body["offer_id"], "request_id": request_body["request_id"]},
    )
    assert match.status in (200, 201)

    order = await client.post(
        f"{AGRO}/orders",
        json={"buyer_id": buyer_body["buyer_id"], "product_id": product_body["product_id"], "quantity": 25},
    )
    assert order.status in (200, 201)
    order_body = await order.json()

    contract = await client.post(
        f"{SC}/export",
        json={
            "action": "contract",
            "buyer": "Export Mill",
            "commodity": "wheat",
            "tons": 25,
            "price": 210,
            "incoterm": "FOB",
        },
    )
    assert contract.status in (200, 201)
    contract_body = await contract.json()
    contract_id = contract_body["contract_id"]

    docs = await client.post(f"{SC}/export", json={"action": "docs", "contract_id": contract_id})
    assert docs.status in (200, 201)

    elev = await client.post(
        f"{SC}/elevator",
        json={"action": "register", "name": "Pilot Elevator", "location": "Nakuru"},
    )
    assert elev.status in (200, 201)

    freight = await client.post(
        f"{SC}/logistics",
        json={"action": "freight", "commodity": "wheat", "tons": 25, "mode": "sea"},
    )
    assert freight.status in (200, 201)

    ports = await client.get(f"{AGRO}/logistics/ports")
    assert ports.status == 200
    ports_body = await ports.json()
    items = ports_body.get("items") or []
    assert items

    carrier = await client.post(
        f"{AGRO}/logistics/carriers",
        json={"name": "SeaAgro Pilot", "countries": ["AE", "NL"], "rating": 4.6, "mode": "sea"},
    )
    assert carrier.status in (200, 201)
    carrier_body = await carrier.json()

    origin = next((p for p in items if p.get("country") == "KE"), items[0])
    dest = next((p for p in items if p.get("country") == "AE"), items[-1])

    ship = await client.post(
        f"{AGRO}/export/shipments",
        json={
            "order_id": order_body["order_id"],
            "contract_id": contract_id,
            "origin_country": "KE",
            "destination_country": dest.get("country", "AE"),
            "origin_port_id": origin.get("port_id"),
            "destination_port_id": dest.get("port_id"),
            "carrier_id": carrier_body.get("carrier_id"),
            "incoterm": "FOB",
            "buyer_id": buyer_body["buyer_id"],
        },
    )
    assert ship.status in (200, 201)
    ship_body = await ship.json()
    shipment_id = ship_body["shipment_id"]

    documents = await client.post(
        f"{AGRO}/export/shipments/{shipment_id}/documents",
        json={"cargo_value": 5250},
    )
    assert documents.status in (200, 201)

    container = await client.post(
        f"{AGRO}/logistics/containers",
        json={"shipment_id": shipment_id, "container_type": "40HC"},
    )
    assert container.status in (200, 201)

    dispatch = await client.post(f"{AGRO}/export/shipments/{shipment_id}/dispatch", json={})
    assert dispatch.status in (200, 201)

    customs = await client.post(f"{AGRO}/export/shipments/{shipment_id}/customs", json={})
    assert customs.status in (200, 201)

    track = await client.get(f"{AGRO}/tracking/{shipment_id}")
    assert track.status == 200

    assert harvest_body.get("harvest_id")


def test_prior_pilots_unchanged_routes():
    web = ROOT / "src" / "web"
    app = (web / "src" / "App.tsx").read_text()
    assert 'path="/workspace/auto"' in app
    assert "AutomotiveLiveWorkflowPage" in app
    assert 'path="/workspace/beauty"' in app
    assert "BeautyLiveWorkflowPage" in app
    assert 'path="/workspace/cafe"' in app
    assert "CafeLiveWorkflowPage" in app
    assert 'path="/workspace/agro"' in app
    assert "AgricultureLiveWorkflowPage" in app
    assert (web / "workspace" / "beauty" / "beautyWorkflow.ts").exists()
    assert (web / "workspace" / "automotive" / "automotiveWorkflow.ts").exists()
    assert (web / "workspace" / "cafe" / "cafeWorkflow.ts").exists()
    assert (web / "workspace" / "agriculture" / "agricultureWorkflow.ts").exists()


def test_agriculture_web_and_reuse_matrix():
    web = ROOT / "src" / "web"
    wf = (web / "workspace" / "agriculture" / "agricultureWorkflow.ts").read_text()
    for needle in (
        "farm_crm",
        "harvest",
        "warehouse",
        "commodity_sale",
        "contract",
        "shipment",
        "stepAiTeamConfigure",
        "quality_gates",
        "runAgricultureLiveWorkflow",
        "agroPrefix",
        "agroSupplyChainPrefix",
    ):
        assert needle in wf, needle
    cfg = (web / "src" / "config" / "webConfig.ts").read_text()
    assert 'sprint: "32.2"' in cfg
    assert "agroPrefix" in cfg
    assert "agroSupplyChainPrefix" in cfg
    tmpl = (web / "workspace" / "ecosystem-template" / "index.ts").read_text()
    assert "agriculture: true" in tmpl
    assert "CROSS_ECOSYSTEM_PATTERNS" in tmpl
    assert "computeReusePercentage" in tmpl
    hub = (web / "src" / "integrations" / "hub.ts").read_text()
    assert "agroSupplyChain" in hub
    assert "aiAgronomist" in hub


def test_reuse_docs_and_manifest():
    text = (ROOT / "docs" / "ECOSYSTEM_REUSE_MATRIX_31_1.md").read_text()
    assert "100%" in text
    assert "Agriculture" in text or "Agro" in text
    assert "Automotive" in text and "Beauty" in text and "Cafe" in text
    report = (ROOT / "docs" / "SPRINT_REPORT_31_1.md").read_text()
    assert "Legal" in report
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.42.0"' in manifest
    assert "32.2" in manifest
    assert "First External Pilot Execution & Product Feedback Loop" in manifest
    index = (ROOT / "docs" / "ARCHITECTURE_AUDIT_INDEX.md").read_text()
    assert "AGRICULTURE_PILOT_EXECUTION_31_1" in index
