"""Tests — Connected Cars, IoT & Telematics (Sprint 13.7)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.register import register_auto_marketplace_routes
from applications.auto_marketplace.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/connected-cars/v1"
AE = "/api/automotive-erp/v1"
SA = "/api/seller-ai/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_auto_marketplace_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    auto_marketplace.reset()
    yield
    auto_marketplace.reset()


def test_version_connected_cars_ready():
    health = auto_marketplace.health()
    assert health["application_version"] == "4.1.7-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v4.1.6-enterprise"
    assert health["connected_cars_ready"] is True
    assert health["telematics_platform_ready"] is True
    assert health["fleet_intelligence_ready"] is True
    assert health["predictive_maintenance_ready"] is True
    assert health["vehicle_iot_platform_ready"] is True


def test_telematics_and_iot():
    suite = auto_marketplace.connected_cars
    vehicle = suite.core.register_vehicle(vin="WVWZZZ1JZXW000001", fleet_id="f1")
    suite.core.connect_vehicle(vehicle["connected_vehicle_id"])
    device = suite.core.register_iot_device(connected_vehicle_id=vehicle["connected_vehicle_id"], kind="obd")
    assert device["kind"] == "obd"
    suite.telematics.track_gps(connected_vehicle_id=vehicle["connected_vehicle_id"], lat=48.1, lon=11.5, speed_kmh=60)
    trip = suite.telematics.start_trip(connected_vehicle_id=vehicle["connected_vehicle_id"], origin="Munich")
    ended = suite.telematics.end_trip(trip["trip_id"], destination="Augsburg", distance_km=70, fuel_liters=5.5, harsh_events=2)
    assert ended["driving_behavior_score"] < 100
    suite.telematics.obd_snapshot(connected_vehicle_id=vehicle["connected_vehicle_id"], codes=["P0300"])
    with pytest.raises(ValidationError):
        suite.core.register_iot_device(connected_vehicle_id=vehicle["connected_vehicle_id"], kind="unknown")


def test_fleet_diagnostics_predictive():
    suite = auto_marketplace.connected_cars
    boot = suite.bootstrap()
    vid = boot["connected_vehicle_id"]
    health = suite.remote.health(vid)
    assert health["health_score"] > 0
    diag = suite.remote.remote_diagnostics(vid)
    assert diag["diagnostics_id"]
    suite.remote.command(connected_vehicle_id=vid, command="lock")
    pred = suite.predictive.predict(connected_vehicle_id=vid, mileage=100000, battery_soc=40, brake_km=50000)
    assert pred["failure_probability"] > 0
    assert pred["maintenance_scheduling"]
    fleet = suite.fleet.dashboard(fleet_id="fleet_eu")
    assert fleet["vehicles"] >= 1
    for dtype in ("connected_fleet", "telematics", "predictive_maintenance", "vehicle_health"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_connected_cars(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "4.1.7-enterprise"
    assert body["connected_cars_ready"] is True
    assert body["telematics_platform_ready"] is True
    assert body["vehicle_iot_platform_ready"] is True

    assert (await client.get(f"{AE}/health")).status == 200
    assert (await client.get(f"{SA}/health")).status == 200

    boot = await client.post(f"{PREFIX}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    gps = await client.post(
        f"{PREFIX}/telematics",
        json={"action": "gps", "connected_vehicle_id": boot_body["connected_vehicle_id"], "lat": 1.0, "lon": 2.0},
    )
    assert gps.status == 201

    pred = await client.post(
        f"{PREFIX}/predictive",
        json={"connected_vehicle_id": boot_body["connected_vehicle_id"], "mileage": 55000},
    )
    assert pred.status == 201

    fleet = await client.get(f"{PREFIX}/fleet?fleet_id=fleet_eu")
    assert fleet.status == 200

    dash = await client.get(f"{PREFIX}/dashboard?type=telematics")
    assert dash.status == 200


def test_docs_and_regression_13_7():
    for name in ("CONNECTED_CARS.md", "TELEMATICS.md", "IOT_PLATFORM.md", "PREDICTIVE_MAINTENANCE.md"):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "CONNECTED_CARS.md").exists()
    assert (ROOT / "applications" / "auto_marketplace" / "connected_cars" / "facade.py").exists()
    for pkg in ("automotive_erp", "seller_ai", "buyer_ai", "dealer_crm", "inspection_ai", "vin_intelligence"):
        assert (ROOT / "applications" / "auto_marketplace" / pkg / "facade.py").exists()
    manifest = (ROOT / "applications" / "auto_marketplace" / "manifest.json").read_text()
    assert "4.1.7-enterprise" in manifest
    assert "13.7" in manifest

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS
    from applications.enterprise.config import DEFAULT_CONFIG as ENT

    assert AIOS.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
