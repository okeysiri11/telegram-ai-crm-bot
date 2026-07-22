"""Tests — Smart Greenhouse, Livestock & CEA (Sprint 14.4)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.agro_enterprise import agro_enterprise
from applications.agro_enterprise.api.register import register_agro_enterprise_routes
from applications.agro_enterprise.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/controlled-environment/v1"
CA = "/api/crop-ai/v1"
SI = "/api/smart-irrigation/v1"
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


def test_version_cea_ready():
    health = agro_enterprise.health()
    assert health["application_version"] == "4.3.7-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v4.3.6-enterprise"
    assert health["smart_greenhouse_ready"] is True
    assert health["livestock_platform_ready"] is True
    assert health["poultry_platform_ready"] is True
    assert health["aquaculture_platform_ready"] is True
    assert health["controlled_environment_agriculture_ready"] is True


def test_greenhouse_and_climate_ai():
    suite = agro_enterprise.controlled_environment
    gh = suite.greenhouse.register_greenhouse(name="GH-1", area_m2=800)
    zone = suite.greenhouse.create_zone(greenhouse_id=gh["greenhouse_id"], name="Bay A")
    suite.greenhouse.set_climate(zone["zone_id"], temp_c=24, humidity_pct=70, co2_ppm=850)
    ctrl = suite.greenhouse.control(zone["zone_id"], control="lighting", enabled=True, setpoint=200)
    assert ctrl["control"] == "lighting"
    opt = suite.climate_ai.optimize(zone_id=zone["zone_id"], temp_c=24, humidity_pct=80)
    assert "humidity_high" in opt["alerts"]
    with pytest.raises(ValidationError):
        suite.greenhouse.control(zone["zone_id"], control="fog", enabled=True)


def test_livestock_poultry_aquaculture():
    suite = agro_enterprise.controlled_environment
    boot = suite.bootstrap()
    assert boot["animal_id"]
    assert boot["flock_id"]
    assert boot["fish_farm_id"]
    suite.livestock.milk(boot["animal_id"], liters=30)
    suite.poultry.record_eggs(boot["flock_id"], count=100)
    water = suite.aquaculture.water_quality(boot["fish_farm_id"], oxygen_mg_l=4.0, temp_c=28)
    assert water["status"] == "low_oxygen"
    for dtype in ("greenhouse", "livestock", "poultry", "aquaculture", "biosecurity", "production"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_controlled_environment(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "4.3.7-enterprise"
    assert body["smart_greenhouse_ready"] is True
    assert body["controlled_environment_agriculture_ready"] is True

    assert (await client.get(f"{CA}/health")).status == 200
    assert (await client.get(f"{SI}/health")).status == 200
    assert (await client.get(f"{PA}/health")).status == 200
    assert (await client.get(f"{AE}/health")).status == 200

    boot = await client.post(f"{PREFIX}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    climate = await client.post(
        f"{PREFIX}/climate-ai",
        json={"zone_id": boot_body["zone_id"], "temp_c": 22, "humidity_pct": 60},
    )
    assert climate.status == 201

    livestock = await client.post(
        f"{PREFIX}/livestock",
        json={"action": "milk", "animal_id": boot_body["animal_id"], "liters": 25},
    )
    assert livestock.status == 201

    dash = await client.get(f"{PREFIX}/dashboard?type=livestock")
    assert dash.status == 200


def test_docs_and_regression_14_4():
    for name in (
        "SMART_GREENHOUSE.md",
        "LIVESTOCK_MANAGEMENT.md",
        "POULTRY_PLATFORM.md",
        "AQUACULTURE.md",
        "BIOSECURITY.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "CONTROLLED_ENVIRONMENT.md").exists()
    assert (ROOT / "applications" / "agro_enterprise" / "controlled_environment" / "facade.py").exists()
    for pkg in ("crop_ai", "smart_irrigation", "precision_agriculture"):
        assert (ROOT / "applications" / "agro_enterprise" / pkg / "facade.py").exists()

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS
    from applications.enterprise.config import DEFAULT_CONFIG as ENT
    from applications.auto_marketplace.config import DEFAULT_CONFIG as AUTO
    from applications.agro_marketplace.config import DEFAULT_CONFIG as AGRO

    assert AIOS.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
    assert AUTO.application_version == "4.2.0-enterprise"
    assert AGRO.application_version == "2.0.0"
    manifest = (ROOT / "applications" / "agro_enterprise" / "manifest.json").read_text()
    assert "4.3.7-enterprise" in manifest
    assert "14.7" in manifest
