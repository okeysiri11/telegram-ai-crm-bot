"""Tests — VTS, AIS, Radar & Navigation (Sprint 15.1)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.port_enterprise import port_enterprise
from applications.port_enterprise.api.register import register_port_enterprise_routes
from applications.port_enterprise.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/port-navigation/v1"
PE = "/api/port-enterprise/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_port_enterprise_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    port_enterprise.reset()
    yield
    port_enterprise.reset()


def test_version_navigation_ready():
    health = port_enterprise.health()
    assert health["application_version"] == "4.5.4-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v4.5.3-enterprise"
    assert health["vts_platform_ready"] is True
    assert health["ais_integration_ready"] is True
    assert health["radar_intelligence_ready"] is True
    assert health["navigation_platform_ready"] is True
    assert health["maritime_safety_ready"] is True


def test_vts_ais_radar():
    suite = port_enterprise.navigation
    center = suite.vts.open_center(name="VTS-1")
    mon = suite.vts.monitor_traffic(center_id=center["center_id"], vessel_count=10, density=0.8)
    assert mon["density_level"] == "high"
    recv = suite.ais.register_receiver(name="AIS-1")
    msg = suite.ais.process_message(
        receiver_id=recv["receiver_id"], mmsi="111", lat=1.0, lon=2.0, sog=8, cog=90
    )
    assert msg["mmsi"] == "111"
    radar = suite.radar.register_radar(name="R1")
    tgt = suite.radar.detect_target(radar_id=radar["radar_id"], bearing=10, range_nm=2, object_class="buoy")
    assert tgt["tracked"] is True
    with pytest.raises(ValidationError):
        suite.radar.detect_target(radar_id=radar["radar_id"], bearing=0, range_nm=1, object_class="plane")


def test_navigation_safety_ai():
    suite = port_enterprise.navigation
    boot = suite.bootstrap()
    assert boot["center_id"] and boot["radar_id"] and boot["risk_id"]
    risk = suite.safety.collision_risk(vessel_a="a", vessel_b="b", score=0.9)
    assert risk["level"] == "critical"
    pred = suite.ai.predict_traffic(area="approaches", horizon_hours=3)
    assert pred["congestion_risk"] >= 0
    with pytest.raises(ValidationError):
        suite.safety.collision_risk(vessel_a="a", vessel_b="b", score=2.0)
    for dtype in ("vts", "ais", "radar", "navigation", "maritime_safety"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_navigation(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "4.5.4-enterprise"
    assert body["vts_platform_ready"] is True
    assert body["maritime_safety_ready"] is True

    assert (await client.get(f"{PE}/health")).status == 200

    boot = await client.post(f"{PREFIX}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    ais = await client.post(
        f"{PREFIX}/ais",
        json={
            "action": "message",
            "receiver_id": boot_body["receiver_id"],
            "mmsi": "999",
            "lat": 46.5,
            "lon": 30.7,
            "sog": 7,
        },
    )
    assert ais.status == 201

    safety = await client.post(
        f"{PREFIX}/safety",
        json={"action": "warning", "title": "Gale", "message": "Force 8 expected"},
    )
    assert safety.status == 201

    dash = await client.get(f"{PREFIX}/dashboard?type=radar")
    assert dash.status == 200


def test_docs_and_regression_15_1():
    for name in (
        "VTS_PLATFORM.md",
        "AIS_INTEGRATION.md",
        "RADAR_SYSTEM.md",
        "NAVIGATION_MANAGEMENT.md",
        "MARITIME_SAFETY.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "PORT_NAVIGATION.md").exists()
    assert (ROOT / "applications" / "port_enterprise" / "navigation" / "facade.py").exists()
    assert (ROOT / "applications" / "port_enterprise" / "application.py").exists()

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS
    from applications.enterprise.config import DEFAULT_CONFIG as ENT
    from applications.auto_marketplace.config import DEFAULT_CONFIG as AUTO
    from applications.agro_enterprise.config import DEFAULT_CONFIG as AGRO
    from applications.port_erp.config import DEFAULT_CONFIG as PORT_ERP

    assert AIOS.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
    assert AUTO.application_version == "4.2.0-enterprise"
    assert AGRO.application_version == "4.4.0-enterprise"
    assert PORT_ERP.application_version == "2.0.0"
    manifest = (ROOT / "applications" / "port_enterprise" / "manifest.json").read_text()
    assert "4.5.4-enterprise" in manifest
    assert "15.4" in manifest
