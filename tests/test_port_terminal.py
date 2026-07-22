"""Tests — Port ERP Terminal Operations (Sprint 9.3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.port_erp import port_erp
from applications.port_erp.api.register import register_port_erp_routes
from applications.port_erp.shared.models import Gate, GateStatus, Warehouse
from applications.port_erp.terminal_operations.models import (
    CycleCount,
    DispatchJob,
    Equipment,
    EquipmentType,
    GateAppointment,
    InventoryItem,
    PlanType,
    TerminalPlan,
    WarehouseOperationType,
    WarehouseTask,
    WarehouseZone,
    YardBlock,
)


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_port_erp_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    port_erp.reset()
    yield
    port_erp.reset()


def test_version_terminal_engine_docs_and_bridges():
    health = port_erp.health()
    assert health["application_version"] == "1.2.0-alpha"
    assert health["terminal_engine"] == "1.0"
    assert "terminal" in health
    docs = Path(__file__).resolve().parents[1] / "docs" / "PORT_TERMINAL.md"
    assert docs.exists()
    assert "Yard Management Engine" in docs.read_text(encoding="utf-8")
    assert port_erp.platform.platform_health()["platform_dependency"] == "AI Platform Core v3"
    assert port_erp.ecosystem.ecosystem_health()["ecosystem_dependency"] == "AI Ecosystem v1.5"
    root = Path(__file__).resolve().parents[1] / "applications" / "port_erp"
    for name in (
        "terminal_operations",
        "yard_management",
        "warehouse_management",
        "gate_management",
        "equipment",
        "cranes",
        "dispatch",
        "planning",
        "storage",
        "inventory",
    ):
        assert (root / name).is_dir()


@pytest.mark.asyncio
async def test_yard_assign_relocate_density():
    block = port_erp.terminal.yard.create_block(
        YardBlock(terminal_id="term-1", name="Block A", rows=2, slots_per_row=2, max_tiers=4)
    )
    assert len(port_erp.terminal.yard.list_slots(block_id=block.block_id)) == 4

    slot = await port_erp.terminal.yard.assign_slot("c-1", terminal_id="term-1", block_id=block.block_id)
    assert slot.container_id == "c-1"
    assert slot.status.value == "occupied"

    relocation = await port_erp.terminal.yard.relocate("c-1", reason="stack_plan")
    assert relocation.container_id == "c-1"
    assert relocation.from_slot_id != relocation.to_slot_id

    plan = port_erp.terminal.yard.stack_plan(block.block_id)
    assert plan["occupied"] == 1
    density = port_erp.terminal.yard.optimize_density(terminal_id="term-1")
    assert density["density"]["occupied"] == 1

    released = await port_erp.terminal.yard.release_container("c-1")
    assert released.status.value == "empty"


@pytest.mark.asyncio
async def test_warehouse_inventory_and_cycle_count():
    wh = port_erp.terminal.warehouse.register_warehouse(
        Warehouse(name="WH-1", terminal_id="term-1", capacity_tons=1000)
    )
    zone = port_erp.terminal.warehouse.create_zone(
        WarehouseZone(warehouse_id=wh.warehouse_id, name="Z1", capacity_units=100)
    )
    item = port_erp.terminal.warehouse.upsert_inventory(
        InventoryItem(
            warehouse_id=wh.warehouse_id,
            zone_id=zone.zone_id,
            sku="SKU-MAIZE",
            description="Maize bags",
            quantity=50,
        )
    )
    assert item.quantity == 50

    task = await port_erp.terminal.warehouse.create_task(
        WarehouseTask(
            warehouse_id=wh.warehouse_id,
            operation=WarehouseOperationType.RECEIVING,
            reference="ASN-1",
        )
    )
    completed = await port_erp.terminal.warehouse.complete_task(task.task_id)
    assert completed.status == "completed"

    movement = await port_erp.terminal.warehouse.move_stock(
        warehouse_id=wh.warehouse_id,
        item_id=item.item_id,
        quantity=10,
        movement_type="out",
        reference="pick-1",
    )
    assert movement.quantity == 10
    updated = port_erp.terminal.warehouse.list_inventory(warehouse_id=wh.warehouse_id)[0]
    assert updated.quantity == 40

    count = await port_erp.terminal.warehouse.cycle_count(
        CycleCount(
            warehouse_id=wh.warehouse_id,
            zone_id=zone.zone_id,
            expected_qty=40,
            counted_qty=39,
        )
    )
    assert count.variance == -1
    assert count.status == "completed"


@pytest.mark.asyncio
async def test_gate_checkin_approve_checkout():
    gate = port_erp.terminal.gate.register_gate(Gate(name="Gate A", terminal_id="term-1"))
    await port_erp.core.operations.open_gate(gate.gate_id)
    opened = port_erp.terminal.gate.get_gate(gate.gate_id)
    assert opened.status == GateStatus.OPEN

    appt = port_erp.terminal.gate.create_appointment(
        GateAppointment(
            gate_id=gate.gate_id,
            plate_number="KCA111A",
            driver_name="Alice",
        )
    )
    visit = await port_erp.terminal.gate.check_in(
        gate_id=gate.gate_id,
        plate_number="KCA111A",
        driver_name="Alice",
        driver_id="drv-1",
        appointment_id=appt.appointment_id,
        qr_payload="driver_id=drv-1&permit=yes",
        ocr_image_ref="plates/KCA111A.jpg",
    )
    assert visit.status.value == "checked_in"
    assert visit.ocr_plate == "KCA111A"
    assert visit.queue_position >= 1

    approved = await port_erp.terminal.gate.approve(visit.visit_id)
    assert approved.access_granted is True
    assert approved.status.value == "approved"

    departed = await port_erp.terminal.gate.check_out(visit.visit_id)
    assert departed.status.value == "checked_out"

    rejected_visit = await port_erp.terminal.gate.check_in(
        gate_id=gate.gate_id,
        plate_number="KZZ999Z",
        driver_id="unknown",
        access_list=["drv-1"],
    )
    assert rejected_visit.status.value == "rejected"


@pytest.mark.asyncio
async def test_equipment_crane_dispatch_planning():
    sts = port_erp.terminal.equipment.register(
        Equipment(name="STS-1", equipment_type=EquipmentType.STS, terminal_id="term-1")
    )
    forklift = port_erp.terminal.equipment.register(
        Equipment(name="FL-1", equipment_type=EquipmentType.FORKLIFT, terminal_id="term-1")
    )
    assert len(port_erp.terminal.equipment.available(terminal_id="term-1")) == 2

    assignment = await port_erp.terminal.cranes.assign(
        vessel_id="vessel-1",
        berth_id="berth-1",
        terminal_id="term-1",
        prefer_type=EquipmentType.STS,
    )
    assert assignment.crane_id == sts.equipment_id
    finished = await port_erp.terminal.cranes.finish(assignment.assignment_id)
    assert finished.status == "finished"

    job = port_erp.terminal.dispatch.create_job(
        DispatchJob(
            terminal_id="term-1",
            job_type="move",
            container_id="c-9",
            from_location="yard",
            to_location="gate",
        )
    )
    assigned = port_erp.terminal.dispatch.assign_equipment(job.job_id, equipment_id=forklift.equipment_id)
    assert assigned.status.value == "assigned"
    started = port_erp.terminal.dispatch.start(job.job_id)
    assert started.status.value == "in_progress"
    done = port_erp.terminal.dispatch.complete(job.job_id)
    assert done.status.value == "completed"

    plan = port_erp.terminal.planning.create_plan(
        TerminalPlan(
            terminal_id="term-1",
            plan_type=PlanType.CRANE,
            title="Morning crane plan",
            resources=[sts.equipment_id],
        )
    )
    active = port_erp.terminal.planning.activate(plan.plan_id)
    assert active.status == "active"
    assert "berth" in port_erp.terminal.planning.plan_types()

    maint = port_erp.terminal.equipment.schedule_maintenance(forklift.equipment_id)
    assert maint.status.value == "maintenance"


@pytest.mark.asyncio
async def test_terminal_rest_api(client: TestClient):
    health = await client.get("/api/port/v1/health")
    assert health.status == 200
    body = await health.json()
    assert body["application_version"] == "1.2.0-alpha"
    assert body["terminal_engine"] == "1.0"

    terminal = await client.get("/api/port/v1/terminal")
    assert terminal.status == 200

    block_resp = await client.post(
        "/api/port/v1/yard/blocks",
        json={"terminal_id": "t1", "name": "Y1", "rows": 1, "slots_per_row": 2},
    )
    assert block_resp.status == 201

    assign = await client.post(
        "/api/port/v1/yard/assign",
        json={"container_id": "API-C1", "terminal_id": "t1"},
    )
    assert assign.status == 200

    wh = await client.post(
        "/api/port/v1/warehouse",
        json={"name": "API-WH", "terminal_id": "t1", "capacity_tons": 500},
    )
    assert wh.status == 201
    warehouse = await wh.json()

    zone = await client.post(
        "/api/port/v1/warehouse/zones",
        json={"warehouse_id": warehouse["warehouse_id"], "name": "Z-A", "capacity_units": 50},
    )
    assert zone.status == 201

    gate_resp = await client.post(
        "/api/port/v1/gate",
        json={"name": "API-Gate", "terminal_id": "t1"},
    )
    assert gate_resp.status == 201
    gate = await gate_resp.json()
    opened = await client.post(f"/api/port/v1/gate/{gate['gate_id']}/open")
    assert opened.status == 200

    checkin = await client.post(
        "/api/port/v1/gate/check-in",
        json={"gate_id": gate["gate_id"], "plate_number": "KBB1", "driver_id": "d1"},
    )
    assert checkin.status == 201

    eq = await client.post(
        "/api/port/v1/equipment",
        json={"name": "RTG-1", "equipment_type": "rtg", "terminal_id": "t1"},
    )
    assert eq.status == 201

    plan = await client.post(
        "/api/port/v1/planning",
        json={"terminal_id": "t1", "plan_type": "yard", "title": "Yard plan"},
    )
    assert plan.status == 201
    plans = await client.get("/api/port/v1/planning")
    assert plans.status == 200
    assert "yard" in (await plans.json())["plan_types"]
