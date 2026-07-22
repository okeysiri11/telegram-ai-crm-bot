"""Tests — Auto Marketplace Fleet & Mobility (Sprint 10.7)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.register import register_auto_marketplace_routes
from applications.auto_marketplace.fleet.models import (
    FleetDispatchJob,
    FleetDriver,
    FleetLeaseKind,
    FleetRegistry,
    FleetVehicle,
    RentalContract,
    RentalKind,
    TelematicsReading,
)


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


def test_version_modules_docs_bridges():
    health = auto_marketplace.health()
    assert health["application_version"] == "4.1.8-enterprise"
    assert health["fleet_engine"] == "1.0"
    assert health["rental_engine"] == "1.0"
    assert health["operations_engine"] == "1.0"
    assert "fleet_ops" in health
    docs = Path(__file__).resolve().parents[1] / "docs" / "AUTO_FLEET.md"
    assert docs.exists() and "4.1.8-enterprise" in docs.read_text(encoding="utf-8")
    assert "4.1.8-enterprise" in (Path(__file__).resolve().parents[1] / "docs" / "AUTO_MARKETPLACE.md").read_text(
        encoding="utf-8"
    )
    assert auto_marketplace.platform.platform_health()["platform_dependency"] == "AI Platform Core v3"
    root = Path(__file__).resolve().parents[1] / "applications" / "auto_marketplace"
    for name in (
        "fleet",
        "rental",
        "leasing",
        "subscriptions",
        "corporate",
        "dispatch",
        "telematics",
        "drivers",
        "operations",
        "executive",
        "mobility",
        "ai_operations",
    ):
        assert (root / name).is_dir()


def test_fleet_engine():
    fleet = auto_marketplace.fleet_ops.fleet.create_fleet(FleetRegistry(name="Corp Fleet", corporate=True))
    vehicle = auto_marketplace.fleet_ops.fleet.register_vehicle(
        FleetVehicle(fleet_id=fleet.fleet_id, vehicle_id="v1", label="Car-1", mileage_km=40000)
    )
    driver = auto_marketplace.fleet_ops.drivers.register(FleetDriver(name="Alex", license_id="L1"))
    assigned = auto_marketplace.fleet_ops.fleet.assign_driver(vehicle.fleet_vehicle_id, driver.driver_id)
    assert assigned.assigned_driver_id == driver.driver_id
    auto_marketplace.fleet_ops.fleet.record_fuel(vehicle.fleet_vehicle_id, liters=40, cost=60, level_pct=80)
    auto_marketplace.fleet_ops.fleet.update_tires(vehicle.fleet_vehicle_id, 55)
    auto_marketplace.fleet_ops.fleet.record_accident(vehicle.fleet_vehicle_id, "Minor bumper", cost=200)
    auto_marketplace.fleet_ops.fleet.plan_maintenance(vehicle.fleet_vehicle_id, due_mileage_km=50000)
    analytics = auto_marketplace.fleet_ops.fleet.analytics(fleet.fleet_id)
    assert analytics["vehicles"] == 1
    assert analytics["total_cost"] >= 260


def test_rental_engine():
    fleet = auto_marketplace.fleet_ops.fleet.create_fleet(FleetRegistry(name="Rental Pool"))
    vehicle = auto_marketplace.fleet_ops.fleet.register_vehicle(
        FleetVehicle(fleet_id=fleet.fleet_id, label="R-1")
    )
    assert auto_marketplace.fleet_ops.rental.availability(fleet.fleet_id)
    priced = auto_marketplace.fleet_ops.rental.price(kind=RentalKind.CORPORATE, days=5)
    assert priced["total_price"] > 0
    rental = auto_marketplace.fleet_ops.rental.reserve(
        RentalContract(
            fleet_vehicle_id=vehicle.fleet_vehicle_id,
            customer_id="c1",
            kind=RentalKind.SHORT,
            daily_rate=50,
        )
    )
    auto_marketplace.fleet_ops.rental.activate(rental.rental_id)
    returned = auto_marketplace.fleet_ops.rental.return_vehicle(rental.rental_id, damage="scratch", damage_cost=30)
    assert returned.status.value == "returned"


def test_dispatch_and_drivers():
    driver = auto_marketplace.fleet_ops.drivers.register(FleetDriver(name="Sam", license_id="L2"))
    auto_marketplace.fleet_ops.drivers.add_training(driver.driver_id, "defensive")
    auto_marketplace.fleet_ops.drivers.rate(driver.driver_id, 4.5)
    auto_marketplace.fleet_ops.drivers.log_hours(driver.driver_id, 8)
    assert auto_marketplace.fleet_ops.drivers.recommend()

    job = auto_marketplace.fleet_ops.dispatch.create_job(FleetDispatchJob(task="Airport pickup", priority=5))
    auto_marketplace.fleet_ops.dispatch.assign(job.job_id, fleet_vehicle_id="fv1", driver_id=driver.driver_id)
    auto_marketplace.fleet_ops.dispatch.schedule_route(job.job_id, ["HQ", "Airport"])
    emergency = auto_marketplace.fleet_ops.dispatch.emergency(task="Breakdown assist")
    assert emergency.emergency
    optimized = auto_marketplace.fleet_ops.dispatch.optimize_queue()
    assert optimized


def test_ai_operations_executive_leasing():
    fleet = auto_marketplace.fleet_ops.fleet.create_fleet(FleetRegistry(name="AI Fleet"))
    vehicle = auto_marketplace.fleet_ops.fleet.register_vehicle(
        FleetVehicle(fleet_id=fleet.fleet_id, label="AI-1", mileage_km=90000, tire_wear_pct=80)
    )
    auto_marketplace.fleet_ops.telematics.ingest(
        TelematicsReading(fleet_vehicle_id=vehicle.fleet_vehicle_id, lat=52.5, lon=13.4, mileage_km=90100, battery_pct=70)
    )
    assert auto_marketplace.fleet_ops.ai_operations.predictive_maintenance(vehicle.fleet_vehicle_id)["recommendation"]
    assert auto_marketplace.fleet_ops.ai_operations.fleet_optimization(fleet.fleet_id)
    assert auto_marketplace.fleet_ops.ai_operations.demand_forecast(7)["forecasted_demand"] >= 1
    assert auto_marketplace.fleet_ops.executive.kpis(fleet.fleet_id)["vehicles"] == 1
    assert auto_marketplace.fleet_ops.executive.live_map(fleet.fleet_id)
    assert "answer" in auto_marketplace.fleet_ops.executive.assistant("utilization?", fleet.fleet_id)

    lease = auto_marketplace.fleet_ops.leasing.quote(
        fleet_vehicle_id=vehicle.fleet_vehicle_id,
        customer_id="c1",
        vehicle_price=30000,
        kind=FleetLeaseKind.FINANCIAL,
    )
    approved = auto_marketplace.fleet_ops.leasing.approve(lease.lease_id)
    assert approved.status == "approved"
    # purchase leasing still works
    from applications.auto_marketplace.transactions.models import LeaseType

    purchase_lease = auto_marketplace.transactions.leasing.quote(
        buyer_id="b1", vehicle_price=20000, lease_type=LeaseType.PERSONAL
    )
    assert purchase_lease.monthly_payment > 0


@pytest.mark.asyncio
async def test_fleet_api_routes(client: TestClient):
    health = await client.get("/api/auto/v1/health")
    body = await health.json()
    assert body["application_version"] == "4.1.8-enterprise"
    assert body["fleet_engine"] == "1.0"

    fleet = await client.post("/api/auto/v1/fleet", json={"name": "API Fleet", "corporate": True})
    assert fleet.status == 201
    fid = (await fleet.json())["fleet_id"]

    vehicle = await client.post(
        "/api/auto/v1/fleet/vehicles",
        json={"fleet_id": fid, "label": "V1", "vehicle_id": "v1"},
    )
    assert vehicle.status == 201
    fvid = (await vehicle.json())["fleet_vehicle_id"]

    driver = await client.post("/api/auto/v1/drivers", json={"name": "Dana", "license_id": "X1"})
    assert driver.status == 201

    rental = await client.post(
        "/api/auto/v1/rental/reserve",
        json={"fleet_vehicle_id": fvid, "customer_id": "c1", "kind": "short_term", "daily_rate": 40},
    )
    assert rental.status == 201

    job = await client.post("/api/auto/v1/dispatch/jobs", json={"task": "Deliver keys", "priority": 2})
    assert job.status == 201

    ops = await client.get("/api/auto/v1/operations")
    assert ops.status == 200

    lease = await client.post(
        "/api/auto/v1/leasing/fleet/quote",
        json={"fleet_vehicle_id": fvid, "customer_id": "c1", "vehicle_price": 25000, "kind": "operational"},
    )
    assert lease.status == 201


def test_platform_untouched():
    root = Path(__file__).resolve().parents[1]
    assert (root / "applications" / "auto_marketplace" / "fleet").is_dir()
    assert not (root / "platform_ai" / "fleet").exists()
    assert (root / "applications" / "auto_marketplace" / "ai_operations" / "engine.py").exists()
