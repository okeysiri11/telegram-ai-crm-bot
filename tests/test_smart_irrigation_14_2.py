"""Tests — Smart Irrigation, Soil & Water (Sprint 14.2)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.agro_enterprise import agro_enterprise
from applications.agro_enterprise.api.register import register_agro_enterprise_routes
from applications.agro_enterprise.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/smart-irrigation/v1"
PA = "/api/precision-agriculture/v1"
AE = "/api/agro-enterprise/v1"


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


def test_version_smart_irrigation_ready():
    health = agro_enterprise.health()
    assert health["application_version"] == "4.4.0-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v4.3.7-enterprise"
    assert health["smart_irrigation_ready"] is True
    assert health["soil_intelligence_ready"] is True
    assert health["water_management_ready"] is True
    assert health["environmental_ai_ready"] is True


def test_soil_and_water():
    suite = agro_enterprise.irrigation
    soil = suite.soil.register_soil(field_id="f1", organic_matter_pct=2.8, ph=6.2)
    assert soil["fertility_score"] > 0
    suite.soil.nutrient_analysis(soil["soil_id"], n=40, p=18, k=150)
    src = suite.water.register_source(name="Pond", source_type="reservoir", capacity_m3=900)
    suite.water.log_consumption(source_id=src["source_id"], volume_m3=20)
    bal = suite.water.water_balance(src["source_id"])
    assert bal["consumed_m3"] == 20
    with pytest.raises(ValidationError):
        suite.water.register_source(name="X", source_type="ocean")


def test_irrigation_iot_ai():
    suite = agro_enterprise.irrigation
    boot = suite.bootstrap()
    zone = boot["zone_id"]
    suite.irrigation.monitor_flow(zone_id=zone, flow_lpm=50, pressure_bar=0.9)
    assert any(f.get("leak_detected") for f in agro_enterprise.store.si_flow.list_all())
    pred = suite.ai.predict(zone_id=zone, soil_moisture_pct=18, et0_mm=6)
    assert pred["irrigation_recommendation"] in ("irrigate", "hold")
    risk = suite.environment.assess_risks(region="Test", soil_moisture_pct=18, temp_c=35)
    assert risk["heat_stress"] > 0
    for dtype in ("irrigation", "water", "soil", "sensor", "ai_recommendation"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_smart_irrigation(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "4.4.0-enterprise"
    assert body["smart_irrigation_ready"] is True
    assert body["soil_intelligence_ready"] is True

    assert (await client.get(f"{PA}/health")).status == 200
    assert (await client.get(f"{AE}/health")).status == 200

    boot = await client.post(f"{PREFIX}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    ai = await client.post(f"{PREFIX}/ai", json={"zone_id": boot_body["zone_id"], "soil_moisture_pct": 25})
    assert ai.status == 201

    env = await client.post(
        f"{PREFIX}/environment",
        json={"action": "risks", "region": "EU", "soil_moisture_pct": 22, "temp_c": 32},
    )
    assert env.status == 201

    dash = await client.get(f"{PREFIX}/dashboard?type=water")
    assert dash.status == 200


def test_docs_and_regression_14_2():
    for name in ("SMART_IRRIGATION.md", "SOIL_INTELLIGENCE.md", "WATER_MANAGEMENT.md", "ENVIRONMENTAL_AI.md"):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "SMART_IRRIGATION.md").exists()
    assert (ROOT / "applications" / "agro_enterprise" / "smart_irrigation" / "facade.py").exists()
    assert (ROOT / "applications" / "agro_enterprise" / "precision_agriculture" / "facade.py").exists()

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS
    from applications.enterprise.config import DEFAULT_CONFIG as ENT
    from applications.auto_marketplace.config import DEFAULT_CONFIG as AUTO
    from applications.agro_marketplace.config import DEFAULT_CONFIG as AGRO

    assert AIOS.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
    assert AUTO.application_version == "4.2.0-enterprise"
    assert AGRO.application_version == "2.0.0"
    manifest = (ROOT / "applications" / "agro_enterprise" / "manifest.json").read_text()
    assert "4.4.0-enterprise" in manifest
    assert "14.8" in manifest
