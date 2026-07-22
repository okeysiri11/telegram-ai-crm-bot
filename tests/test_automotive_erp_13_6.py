"""Tests — Automotive ERP, Fleet & Predictive Maintenance (Sprint 13.6)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.register import register_auto_marketplace_routes
from applications.auto_marketplace.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/automotive-erp/v1"
SA = "/api/seller-ai/v1"
BA = "/api/buyer-ai/v1"
DC = "/api/dealer-crm/v1"


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


def test_version_automotive_erp_ready():
    health = auto_marketplace.health()
    assert health["application_version"] == "4.1.7-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v4.1.6-enterprise"
    assert health["automotive_erp_ready"] is True
    assert health["fleet_management_ready"] is True
    assert health["predictive_maintenance_ready"] is True
    assert health["enterprise_service_platform_ready"] is True


def test_service_center():
    suite = auto_marketplace.automotive_erp
    mech = suite.service.register_mechanic(name="Jordan Mech", specialty="brakes")
    so = suite.service.create_service_order(vin="1HGCM82633A000001", customer="Fleet Co", warranty=True)
    ro = suite.service.create_repair_order(service_order_id=so["service_order_id"], tasks=["pads"], parts=["BRAKE-PAD-F"])
    assert ro["repair_order_id"]
    suite.service.schedule(so["service_order_id"], mechanic_id=mech["mechanic_id"], starts_at="2026-07-26T10:00:00Z")
    hist = suite.service.quality_control(so["service_order_id"], passed=True)
    assert hist["result"] == "passed"
    with pytest.raises(ValidationError):
        suite.service.create_service_order(vin="SHORT")


def test_fleet_management():
    suite = auto_marketplace.automotive_erp
    fleet = suite.fleet.create_fleet(name="City Fleet", operator="CityOps")
    vehicle = suite.fleet.add_vehicle(fleet_id=fleet["fleet_id"], vin="WVWZZZ1JZXW000001", label="Van-1")
    driver = suite.fleet.register_driver(name="Lee Driver", license_id="DL-9")
    suite.fleet.assign_vehicle(fleet_vehicle_id=vehicle["fleet_vehicle_id"], driver_id=driver["driver_id"])
    trip = suite.fleet.log_trip(fleet_vehicle_id=vehicle["fleet_vehicle_id"], distance_km=80, fuel_liters=7)
    assert trip["distance_km"] == 80
    suite.fleet.schedule_maintenance(fleet_vehicle_id=vehicle["fleet_vehicle_id"], due_at="2026-09-01T00:00:00Z")
    dash = suite.fleet.dashboard(fleet["fleet_id"])
    assert dash["vehicles"] == 1
    assert dash["avg_utilization"] > 0


def test_parts_and_enterprise_erp():
    suite = auto_marketplace.automotive_erp
    part = suite.parts.add_part(sku="FILTER-OIL", name="Oil Filter", qty=10, unit_cost=12)
    supplier = suite.parts.register_supplier(name="Parts Plus")
    po = suite.parts.create_purchase_order(supplier_id=supplier["supplier_id"], items=[{"sku": "FILTER-OIL", "qty": 100}])
    assert po["status"] == "open"
    suite.parts.reserve(part_id=part["part_id"], qty=2, ref="so-1")
    suite.parts.track_serial(part_id=part["part_id"], serial="SN-OF-1")
    fc = suite.parts.forecast(warehouse="main")
    assert fc["skus"] >= 1
    inv = suite.enterprise.create_invoice(customer="Acme", amount=500)
    assert inv["invoice_id"]
    suite.enterprise.create_contract(party="Acme", contract_type="fleet_service")
    suite.enterprise.procurement_request(title="Filters", budget=1200)
    suite.enterprise.portal_access(portal="customer", principal="ops@acme.example")


def test_maintenance_ai_and_analytics():
    suite = auto_marketplace.automotive_erp
    pred = suite.maintenance_ai.predict(vin="1HGCM82633A000001", mileage=90000, health_score=65, recent_failures=2)
    assert pred["failure_probability"] > 0.3
    assert pred["downtime_prediction_days"] >= 1
    assert pred["repair_recommendations"]
    suite.integrations.connect(target="vin_intelligence", endpoint="/api/vin-intelligence/v1")
    suite.integrations.connect(target="ai_os", endpoint="/api/ai-os/v1")
    for rt in ("fleet", "service", "cost", "profit", "inventory", "executive"):
        assert suite.analytics.report(report_type=rt)["report_type"] == rt


@pytest.mark.asyncio
async def test_api_automotive_erp(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "4.1.7-enterprise"
    assert body["automotive_erp_ready"] is True
    assert body["fleet_management_ready"] is True
    assert body["predictive_maintenance_ready"] is True

    assert (await client.get(f"{SA}/health")).status == 200
    assert (await client.get(f"{BA}/health")).status == 200
    assert (await client.get(f"{DC}/health")).status == 200

    boot = await client.post(f"{PREFIX}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()
    assert boot_body["fleet_id"]

    fleet = await client.get(f"{PREFIX}/fleet?fleet_id={boot_body['fleet_id']}")
    assert fleet.status == 200

    maint = await client.post(
        f"{PREFIX}/maintenance",
        json={"vin": "WBA3A5C50EF000001", "mileage": 60000, "health_score": 78},
    )
    assert maint.status == 201

    analytics = await client.get(f"{PREFIX}/analytics?type=executive")
    assert analytics.status == 200

    parts = await client.post(f"{PREFIX}/parts", json={"sku": "WIPER-F", "name": "Wiper", "qty": 5})
    assert parts.status == 201


def test_docs_and_regression_13_6():
    for name in ("AUTOMOTIVE_ERP.md", "FLEET_MANAGEMENT.md", "SERVICE_CENTER.md", "PREDICTIVE_MAINTENANCE.md"):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "AUTOMOTIVE_ERP.md").exists()
    assert (ROOT / "applications" / "auto_marketplace" / "automotive_erp" / "facade.py").exists()
    for pkg in ("seller_ai", "buyer_ai", "dealer_crm", "inspection_ai", "vin_intelligence", "enterprise_automotive"):
        assert (ROOT / "applications" / "auto_marketplace" / pkg / "facade.py").exists()
    manifest = (ROOT / "applications" / "auto_marketplace" / "manifest.json").read_text()
    assert "4.1.7-enterprise" in manifest
    assert "13.7" in manifest

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS
    from applications.enterprise.config import DEFAULT_CONFIG as ENT

    assert AIOS.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
