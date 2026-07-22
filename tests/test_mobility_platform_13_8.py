"""Tests — Mobility Intelligence, EV & Smart City (Sprint 13.8)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.register import register_auto_marketplace_routes
from applications.auto_marketplace.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/mobility-platform/v1"
CC = "/api/connected-cars/v1"
AE = "/api/automotive-erp/v1"


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


def test_version_mobility_ready():
    health = auto_marketplace.health()
    assert health["application_version"] == "4.1.8-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v4.1.7-enterprise"
    assert health["mobility_platform_ready"] is True
    assert health["smart_transportation_ready"] is True
    assert health["ev_ecosystem_ready"] is True
    assert health["logistics_intelligence_ready"] is True
    assert health["smart_city_integration_ready"] is True


def test_mobility_and_ev():
    suite = auto_marketplace.mobility_platform
    hub = suite.hub.create_hub(name="Test Hub", city="Vienna")
    plan = suite.hub.travel_plan(origin="A", destination="B")
    suite.hub.optimize_trip(plan_id=plan["plan_id"])
    ev = suite.ev.register_ev(vin="1HGCM82633A000001", model="Model 3", battery_kwh=75)
    suite.ev.battery_health(ev["ev_id"], soh_pct=88, cycles=500)
    charger = suite.ev.register_charger(name="DC Fast", kw=120)
    sess = suite.ev.start_session(ev_id=ev["ev_id"], charger_id=charger["charger_id"])
    suite.ev.end_session(sess["session_id"], kwh_delivered=22)
    rang = suite.ev.range_prediction(ev_id=ev["ev_id"], soc_pct=60)
    assert rang["predicted_range_km"] > 0
    offering = suite.maas.create_offering(name="ShareX", service_type="ride_share")
    suite.maas.reserve(offering_id=offering["offering_id"], user="u1", starts_at="2026-08-01T10:00:00Z")
    with pytest.raises(ValidationError):
        suite.maas.create_offering(name="Bad", service_type="teleport")
    assert hub["hub_id"]


def test_transport_logistics_smart_city():
    suite = auto_marketplace.mobility_platform
    suite.transport.traffic_flow(corridor="Ring", vehicles_per_hour=2000)
    suite.transport.congestion_prediction(region="Vienna")
    suite.transport.parking_availability(zone="Innere", available=10, capacity=50)
    ship = suite.logistics.create_shipment(cargo="Boxes", origin="WH", destination="Store")
    suite.logistics.optimize_delivery(shipment_id=ship["shipment_id"], stops=["A", "B"])
    suite.logistics.dispatch(vehicle_id="v1", shipment_id=ship["shipment_id"])
    suite.ai.demand_forecast(region="Vienna")
    suite.ai.carbon_footprint(trips=2, mode="metro")
    suite.smart_city.register_asset(kind="parking", name="Garage-1")
    urban = suite.smart_city.urban_dashboard(city="Vienna")
    assert urban["city"] == "Vienna"
    for dtype in ("mobility", "transportation", "ev", "logistics", "smart_city", "sustainability"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_mobility_platform(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "4.1.8-enterprise"
    assert body["mobility_platform_ready"] is True
    assert body["ev_ecosystem_ready"] is True
    assert body["smart_city_integration_ready"] is True

    assert (await client.get(f"{CC}/health")).status == 200
    assert (await client.get(f"{AE}/health")).status == 200

    boot = await client.post(f"{PREFIX}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    ev = await client.post(f"{PREFIX}/ev", json={"action": "range", "ev_id": boot_body["ev_id"], "soc_pct": 80})
    assert ev.status == 201

    transport = await client.post(f"{PREFIX}/transport", json={"action": "parking", "zone": "Z1", "available": 5, "capacity": 20})
    assert transport.status == 201

    logistics = await client.post(
        f"{PREFIX}/logistics",
        json={"cargo": "API pallet", "origin": "A", "destination": "B"},
    )
    assert logistics.status == 201

    city = await client.get(f"{PREFIX}/smart-city?city=Berlin")
    assert city.status == 200

    dash = await client.get(f"{PREFIX}/dashboard?type=sustainability")
    assert dash.status == 200


def test_docs_and_regression_13_8():
    for name in (
        "MOBILITY_PLATFORM.md",
        "SMART_TRANSPORTATION.md",
        "EV_ECOSYSTEM.md",
        "LOGISTICS_AI.md",
        "SMART_CITY.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "MOBILITY_PLATFORM.md").exists()
    assert (ROOT / "applications" / "auto_marketplace" / "mobility_platform" / "facade.py").exists()
    for pkg in ("connected_cars", "automotive_erp", "seller_ai", "buyer_ai", "dealer_crm"):
        assert (ROOT / "applications" / "auto_marketplace" / pkg / "facade.py").exists()
    manifest = (ROOT / "applications" / "auto_marketplace" / "manifest.json").read_text()
    assert "4.1.8-enterprise" in manifest
    assert "13.8" in manifest

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS
    from applications.enterprise.config import DEFAULT_CONFIG as ENT

    assert AIOS.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
