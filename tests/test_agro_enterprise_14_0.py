"""Tests — Agro Enterprise Foundation & AI Marketplace (Sprint 14.0)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.agro_enterprise import agro_enterprise
from applications.agro_enterprise.api.register import register_agro_enterprise_routes
from applications.agro_enterprise.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/agro-enterprise/v1"


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
def reset_store():
    agro_enterprise.reset()
    yield
    agro_enterprise.reset()


def test_version_agro_enterprise_ready():
    health = agro_enterprise.health()
    assert health["application_version"] == "4.3.6-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v4.3.5-enterprise"
    assert health["agro_marketplace_ready"] is True
    assert health["farm_registry_ready"] is True
    assert health["crop_management_ready"] is True
    assert health["agro_crm_ready"] is True


def test_marketplace():
    boot = agro_enterprise.bootstrap()
    assert boot["order_id"]
    listing = agro_enterprise.marketplace.create_listing(
        category="seeds", side="sell", title="Barley seed", quantity=2, price=900
    )
    assert listing["status"] == "open"
    dirs = agro_enterprise.marketplace.directories()
    assert dirs["suppliers"] and dirs["buyers"]
    with pytest.raises(ValidationError):
        agro_enterprise.marketplace.create_listing(category="ore", side="sell", title="x")


def test_farm_and_crops():
    farm = agro_enterprise.farms.create_farm(name="River Farm", hectares=100)
    land = agro_enterprise.farms.register_farmland(farm_id=farm["farm_id"], label="Plot A", hectares=40)
    agro_enterprise.farms.add_certification(farm_id=farm["farm_id"], standard="GlobalGAP")
    crop = agro_enterprise.crops.add_crop(name="Sunflower", variety="LG")
    agro_enterprise.crops.assign_field(farm_id=farm["farm_id"], land_id=land["land_id"], crop_id=crop["crop_id"])
    plan = agro_enterprise.crops.yield_plan(crop_id=crop["crop_id"], hectares=40, expected_t_per_ha=2.8)
    assert plan["expected_total_t"] == 112.0


def test_crm_and_knowledge():
    contact = agro_enterprise.crm.create_contact(name="Anna", crm_type="buyer")
    agro_enterprise.crm.create_contract(party_id=contact["contact_id"], title="Seed supply", value=10000)
    agro_enterprise.crm.create_lead(name="Coop East")
    article = agro_enterprise.knowledge.publish(base="crop", title="Maize density", body="70k plants/ha")
    assert article["graph_node"]
    assert agro_enterprise.knowledge.search(query="Maize")
    for dtype in ("marketplace", "farm", "production", "sales", "executive"):
        assert agro_enterprise.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_agro_enterprise(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "4.3.6-enterprise"
    assert body["agro_marketplace_ready"] is True
    assert body["farm_registry_ready"] is True

    boot = await client.post(f"{PREFIX}/bootstrap", json={})
    assert boot.status == 201

    mp = await client.post(
        f"{PREFIX}/marketplace",
        json={"category": "fertilizers", "side": "buy", "title": "Urea", "quantity": 10, "price": 400},
    )
    assert mp.status == 201

    farms = await client.get(f"{PREFIX}/farms")
    assert farms.status == 200

    crm = await client.post(f"{PREFIX}/crm", json={"name": "API Farmer", "crm_type": "farmer"})
    assert crm.status == 201

    kb = await client.get(f"{PREFIX}/knowledge?q=wheat")
    assert kb.status == 200

    dash = await client.get(f"{PREFIX}/dashboard?type=production")
    assert dash.status == 200


def test_docs_and_regression_14_0():
    for name in ("AGRO_PLATFORM.md", "AGRO_MARKETPLACE.md", "FARM_REGISTRY.md", "CROP_MANAGEMENT.md"):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "AGRO_ENTERPRISE.md").exists()
    assert (ROOT / "applications" / "agro_enterprise" / "application.py").exists()
    assert (ROOT / "applications" / "agro_enterprise" / "manifest.json").exists()

    # Untouched platforms
    from applications.ai_os.config import DEFAULT_CONFIG as AIOS
    from applications.enterprise.config import DEFAULT_CONFIG as ENT
    from applications.auto_marketplace.config import DEFAULT_CONFIG as AUTO
    from applications.agro_marketplace.config import DEFAULT_CONFIG as AGRO

    assert AIOS.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
    assert AUTO.application_version == "4.2.0-enterprise"
    assert AGRO.application_version == "2.0.0"
    assert (ROOT / "applications" / "auto_marketplace" / "enterprise_certification" / "facade.py").exists()
    manifest = (ROOT / "applications" / "agro_enterprise" / "manifest.json").read_text()
    assert "4.3.6-enterprise" in manifest
    assert "14.6" in manifest
    assert "auto_marketplace" in manifest
    # Sprint 14.0 foundation docs remain
    assert (ROOT / "docs" / "AGRO_PLATFORM.md").exists()
    assert (ROOT / "applications" / "agro_enterprise" / "precision_agriculture" / "facade.py").exists()
