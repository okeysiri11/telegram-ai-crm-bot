"""Tests — Precision Agriculture, GIS & Smart Fields (Sprint 14.1)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.agro_enterprise import agro_enterprise
from applications.agro_enterprise.api.register import register_agro_enterprise_routes
from applications.agro_enterprise.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/precision-agriculture/v1"
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


def test_version_precision_ready():
    health = agro_enterprise.health()
    assert health["application_version"] == "4.3.4-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v4.3.3-enterprise"
    assert health["precision_agriculture_ready"] is True
    assert health["gis_platform_ready"] is True
    assert health["drone_integration_ready"] is True
    assert health["satellite_intelligence_ready"] is True
    assert health["smart_fields_ready"] is True


def test_gis_and_fields():
    suite = agro_enterprise.precision
    field = suite.fields.register_field(name="Plot B", hectares=12, soil_type="sandy_loam")
    suite.fields.set_boundary(
        field["field_id"],
        coordinates=[{"lat": 1.0, "lon": 2.0}, {"lat": 1.1, "lon": 2.0}, {"lat": 1.1, "lon": 2.1}],
    )
    gmap = suite.gis.create_map(name="Plot B Map", field_id=field["field_id"])
    suite.gis.add_layer(gmap["map_id"], layer="ndvi")
    assert suite.fields.analytics(field["field_id"])["boundary_points"] == 3
    with pytest.raises(ValidationError):
        suite.gis.add_layer(gmap["map_id"], layer="radar")


def test_drone_satellite_iot_ai():
    suite = agro_enterprise.precision
    boot = suite.bootstrap()
    fid = boot["field_id"]
    assert boot["flight_id"]
    assert suite.satellite.timeline(fid)
    iot = suite.iot.dashboard(fid)
    assert iot["sensors"] >= 1
    ai = suite.ai.analyze(field_id=fid, ndvi=0.4, stress_index=0.5, growth_day=110)
    assert ai["harvest_readiness"] is True
    for dtype in ("field", "drone", "satellite", "iot", "crop_health"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_precision_agriculture(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "4.3.4-enterprise"
    assert body["precision_agriculture_ready"] is True
    assert body["drone_integration_ready"] is True

    assert (await client.get(f"{AE}/health")).status == 200

    boot = await client.post(f"{PREFIX}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    gis = await client.post(
        f"{PREFIX}/gis",
        json={"action": "layer", "map_id": boot_body["map_id"], "layer": "topo"},
    )
    assert gis.status == 201

    sat = await client.post(
        f"{PREFIX}/satellite",
        json={"action": "analyze", "imagery_id": boot_body["imagery_id"]},
    )
    assert sat.status == 201

    ai = await client.post(f"{PREFIX}/ai", json={"field_id": boot_body["field_id"], "ndvi": 0.7})
    assert ai.status == 201

    dash = await client.get(f"{PREFIX}/dashboard?type=iot")
    assert dash.status == 200


def test_docs_and_regression_14_1():
    for name in (
        "PRECISION_AGRICULTURE.md",
        "GIS_PLATFORM.md",
        "DRONE_AGRO.md",
        "SMART_FIELDS.md",
        "SATELLITE_AI.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "PRECISION_AGRICULTURE.md").exists()
    assert (ROOT / "applications" / "agro_enterprise" / "precision_agriculture" / "facade.py").exists()
    assert (ROOT / "applications" / "agro_enterprise" / "application.py").exists()

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS
    from applications.enterprise.config import DEFAULT_CONFIG as ENT
    from applications.auto_marketplace.config import DEFAULT_CONFIG as AUTO
    from applications.agro_marketplace.config import DEFAULT_CONFIG as AGRO

    assert AIOS.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
    assert AUTO.application_version == "4.2.0-enterprise"
    assert AGRO.application_version == "2.0.0"
    manifest = (ROOT / "applications" / "agro_enterprise" / "manifest.json").read_text()
    assert "4.3.4-enterprise" in manifest
    assert "14.4" in manifest
