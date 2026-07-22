"""Tests — Auto Marketplace Service & Parts (Sprint 10.5)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.register import register_auto_marketplace_routes
from applications.auto_marketplace.service_centers.models import (
    DiagnosticReport,
    MaintenancePlan,
    Part,
    PartKind,
    PartsWarehouse,
    PurchaseOrder,
    RepairOrder,
    ServiceAppointment,
    ServiceCenter,
    StockItem,
    Supplier,
    VehicleServiceRecord,
    WarrantyKind,
    WarrantyPolicy,
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
    assert health["application_version"] == "4.1.5-enterprise"
    assert health["service_engine"] == "1.0"
    assert health["parts_engine"] == "1.0"
    assert health["maintenance_engine"] == "1.0"
    assert "service" in health
    docs = Path(__file__).resolve().parents[1] / "docs" / "AUTO_SERVICE.md"
    assert docs.exists()
    assert "4.1.5-enterprise" in docs.read_text(encoding="utf-8")
    mp = Path(__file__).resolve().parents[1] / "docs" / "AUTO_MARKETPLACE.md"
    assert "4.1.5-enterprise" in mp.read_text(encoding="utf-8")
    assert auto_marketplace.platform.platform_health()["platform_dependency"] == "AI Platform Core v3"
    root = Path(__file__).resolve().parents[1] / "applications" / "auto_marketplace"
    for name in (
        "service_centers",
        "repair_orders",
        "maintenance",
        "appointments",
        "parts",
        "inventory",
        "suppliers",
        "warranty",
        "diagnostics",
        "service_history",
    ):
        assert (root / name).is_dir()


def test_service_centers_and_repair_orders():
    center = auto_marketplace.service.centers.create_center(
        ServiceCenter(name="North Branch", branch_code="N-01", address="1 Main")
    )
    order = auto_marketplace.service.repair_orders.accept(
        RepairOrder(center_id=center.center_id, vehicle_id="v1", customer_id="c1", vin="JTDBR32E720123456")
    )
    auto_marketplace.service.centers.enqueue(center.center_id, order.order_id, priority=1)
    assert auto_marketplace.service.centers.queue(center.center_id)
    auto_marketplace.service.repair_orders.inspect(order.order_id, [{"item": "pads", "ok": False}])
    auto_marketplace.service.repair_orders.estimate(order.order_id, 320)
    auto_marketplace.service.repair_orders.approve(order.order_id)
    started = auto_marketplace.service.repair_orders.start(order.order_id)
    assert started.status.value == "in_progress"
    auto_marketplace.service.repair_orders.progress(order.order_id, "Pads replaced")
    completed = auto_marketplace.service.repair_orders.complete(order.order_id)
    assert completed.status.value == "completed"
    delivered = auto_marketplace.service.repair_orders.deliver(order.order_id)
    assert delivered.status.value == "delivered"


def test_maintenance_engine():
    plan = auto_marketplace.service.maintenance.create_plan(
        MaintenancePlan(vehicle_id="v1", name="Annual", interval_km=10000, interval_days=365)
    )
    sched = auto_marketplace.service.maintenance.schedule(plan_id=plan.plan_id, current_mileage_km=50000)
    assert sched.due_mileage_km == 60000
    due = auto_marketplace.service.maintenance.track_mileage("v1", 60000)
    assert due
    reminders = auto_marketplace.service.maintenance.reminders(vehicle_id="v1")
    assert reminders
    fleet = auto_marketplace.service.maintenance.create_plan(
        MaintenancePlan(fleet_id="fleet-1", name="Fleet A", vehicle_id="")
    )
    assert auto_marketplace.service.maintenance.fleet_plans("fleet-1")
    assert fleet.plan_id


def test_parts_and_inventory():
    supplier = auto_marketplace.service.suppliers.register(Supplier(name="OEM Direct", country="JP", rating=4.8))
    part = auto_marketplace.service.parts.add_part(
        Part(
            sku="OIL-01",
            name="Oil filter",
            kind=PartKind.OEM,
            supplier_id=supplier.supplier_id,
            price=25,
            compatible_vins=["JTDBR32E720123456"],
            compatible_makes=["Toyota"],
        )
    )
    assert auto_marketplace.service.parts.compare_prices("oil")
    assert auto_marketplace.service.parts.compatible_by_vin("JTDBR32E720123456")
    wh = auto_marketplace.service.inventory.create_warehouse(
        PartsWarehouse(name="Parts WH", center_id="c1", location="Aisle 1")
    )
    auto_marketplace.service.inventory.upsert_stock(
        StockItem(warehouse_id=wh.warehouse_id, part_id=part.part_id, quantity=2, min_quantity=5)
    )
    alerts = auto_marketplace.service.inventory.low_stock_alerts()
    assert alerts
    po = auto_marketplace.service.inventory.create_po(
        PurchaseOrder(
            supplier_id=supplier.supplier_id,
            warehouse_id=wh.warehouse_id,
            lines=[{"part_id": part.part_id, "quantity": 10}],
        )
    )
    received = auto_marketplace.service.inventory.receive_po(po.po_id)
    assert received.status == "received"
    reservation = auto_marketplace.service.inventory.reserve(
        warehouse_id=wh.warehouse_id, part_id=part.part_id, quantity=1
    )
    assert reservation["status"] == "reserved"
    assert auto_marketplace.service.parts.availability(part.part_id)["available"] >= 0


def test_appointments_warranty_diagnostics_history():
    center = auto_marketplace.service.centers.create_center(ServiceCenter(name="East", branch_code="E-01"))
    appt = auto_marketplace.service.appointments.book(
        ServiceAppointment(center_id=center.center_id, customer_id="c1", vehicle_id="v1")
    )
    auto_marketplace.service.appointments.allocate(appt.appointment_id, mechanic_id="m1", bay_id="b1")
    resched = auto_marketplace.service.appointments.reschedule(appt.appointment_id, starts_at=appt.starts_at + 7200)
    assert resched.status.value == "rescheduled"

    warranty = auto_marketplace.service.warranty.register(
        WarrantyPolicy(vehicle_id="v1", vin="JTDBR32E720123456", provider="OEM", kind=WarrantyKind.MANUFACTURER)
    )
    assert auto_marketplace.service.warranty.validate(warranty.warranty_id, mileage_km=10000)["valid"]
    claim = auto_marketplace.service.warranty.open_claim(warranty_id=warranty.warranty_id, description="Sensor")
    assert claim.status == "open"

    report = auto_marketplace.service.diagnostics.create_report(
        DiagnosticReport(vehicle_id="v1", obd_codes=["P0300"], damage=["bumper"], photos=["a.jpg"])
    )
    assert report.recommendations

    auto_marketplace.service.history.add(
        VehicleServiceRecord(vehicle_id="v1", kind="maintenance", title="Oil change", mileage_km=50000)
    )
    auto_marketplace.service.history.add(
        VehicleServiceRecord(vehicle_id="v1", kind="warranty", title="Sensor claim", details={"claim_id": claim.claim_id})
    )
    history = auto_marketplace.service.history.complete_history("v1")
    assert history["total"] >= 2
    assert history["maintenance"]


@pytest.mark.asyncio
async def test_service_api_routes(client: TestClient):
    health = await client.get("/api/auto/v1/health")
    body = await health.json()
    assert body["application_version"] == "4.1.5-enterprise"
    assert body["service_engine"] == "1.0"

    center = await client.post("/api/auto/v1/service/centers", json={"name": "API Center", "branch_code": "A1"})
    assert center.status == 201
    cid = (await center.json())["center_id"]

    order = await client.post(
        "/api/auto/v1/service/orders",
        json={"center_id": cid, "vehicle_id": "v1", "customer_id": "c1"},
    )
    assert order.status == 201

    plan = await client.post(
        "/api/auto/v1/maintenance/plans",
        json={"vehicle_id": "v1", "interval_km": 8000},
    )
    assert plan.status == 201

    part = await client.post(
        "/api/auto/v1/parts",
        json={"sku": "FLT-1", "name": "Cabin filter", "kind": "aftermarket", "price": 40},
    )
    assert part.status == 201

    inv = await client.get("/api/auto/v1/inventory")
    assert inv.status == 200

    appt = await client.post(
        "/api/auto/v1/appointments",
        json={"center_id": cid, "customer_id": "c1", "vehicle_id": "v1"},
    )
    assert appt.status == 201

    warranty = await client.post(
        "/api/auto/v1/warranty",
        json={"vehicle_id": "v1", "provider": "OEM", "kind": "extended"},
    )
    assert warranty.status == 201


def test_platform_untouched():
    root = Path(__file__).resolve().parents[1]
    assert (root / "applications" / "auto_marketplace" / "service_centers").is_dir()
    # Sprint 10.5 must not introduce service code outside auto_marketplace
    assert not (root / "platform_ai" / "service_centers").exists()
    assert (root / "applications" / "auto_marketplace" / "parts" / "engine.py").exists()
