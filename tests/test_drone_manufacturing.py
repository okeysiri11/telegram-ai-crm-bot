"""Tests — Drone Manufacturing & Production (Sprint 11.6)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.drone_platform import drone_platform
from applications.drone_platform.api.register import register_drone_platform_routes


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/drone/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_drone_platform_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    drone_platform.reset()
    yield
    drone_platform.reset()


def test_version_manufacturing_ready():
    health = drone_platform.health()
    assert health["application_version"] == "1.8.0-alpha"
    assert health["drone_manufacturing_ready"] is True
    assert health["assembly_platform_ready"] is True
    assert health["warehouse_ready"] is True
    assert health["production_ai_ready"] is True
    assert health["quality_assurance_ready"] is True
    assert health["lifecycle_management_ready"] is True
    assert health["engines"]["manufacturing_suite"] == "1.0"
    assert health["engines"]["ai"] == "1.8"


def test_production_assembly_bom_workflow():
    mfg = drone_platform.manufacturing_suite
    wc = mfg.production.create_work_center(name="ASM-1", center_type="assembly")
    order = mfg.production.create_order(product_name="Quad X450", quantity=2, revision="A")
    plan = mfg.production.plan(order_id=order["order_id"], work_center_id=wc["work_center_id"])
    assert plan["status"] == "scheduled"
    mfg.production.calendar_event(title="Build day", date="2026-07-22", order_id=order["order_id"])
    tmpl = mfg.assembly.create_template(name="Quad template")
    mfg.assembly.create_work_instruction(title="Motor mount", steps=[{"step": 1, "text": "Torque to 2Nm"}], template_id=tmpl["template_id"])
    asm = mfg.assembly.start_assembly(order_id=order["order_id"], template_id=tmpl["template_id"])
    assert asm["status"] == "in_progress"
    mfg.assembly.complete_step(asm["assembly_id"])
    bom = mfg.bom.create(
        name="Quad BOM",
        bom_type="manufacturing",
        lines=[{"sku": "MOT-2212", "qty": 4, "unit_cost": 20}, {"sku": "FC-H743", "qty": 1, "unit_cost": 80}],
        alternatives={"MOT-2212": ["MOT-2208"]},
    )
    cost = mfg.bom.cost_calculator(bom["bom_id"])
    assert cost["total_cost"] == 160.0
    wh = drone_platform.inventory.create_warehouse(name="Main")
    mfg.warehouse.receive_components(warehouse_id=wh.warehouse_id, component_type="motors", sku="MOT-2212", quantity=2, serial_numbers=["M1", "M2"])
    avail = mfg.bom.availability_checker(bom["bom_id"], warehouse_id=wh.warehouse_id)
    assert avail["fully_available"] is False
    procure = mfg.bom.procurement_suggestions(bom["bom_id"], warehouse_id=wh.warehouse_id)
    assert procure["count"] >= 1
    job = mfg.workflow.start_job(order_id=order["order_id"], assembly_id=asm["assembly_id"], serial_number=asm["serial_number"])
    advanced = mfg.workflow.advance(job["job_id"])
    assert advanced["current_stage"] == "incoming_inspection"


def test_programming_calibration_qa_flight_lifecycle():
    mfg = drone_platform.manufacturing_suite
    sn = mfg.programming.assign_serial_number()["serial_number"]
    assert mfg.programming.flash_firmware(serial_number=sn, firmware_version="4.5.0")["status"] == "flashed"
    assert mfg.programming.upload_parameters(serial_number=sn, parameters={"BATT_CAPACITY": 5000})["status"] == "uploaded"
    assert mfg.programming.qr_code_generator(serial_number=sn)["qr_token"]
    mfg.programming.device_registration(serial_number=sn, model="X450")
    suite = mfg.calibration.run_suite(serial_number=sn, types=["accelerometer", "compass", "esc"])
    assert suite["passed"] is True
    qa = mfg.qa.run_full_checklist(serial_number=sn)
    assert qa["passed"] is True
    cert = mfg.qa.final_certification(serial_number=sn)
    assert cert["certified"] is True
    for t in ("bench", "motor", "hover", "autonomous", "waypoint", "safety"):
        mfg.flight_tests.run_test(serial_number=sn, test_type=t)
    acceptance = mfg.flight_tests.acceptance_protocol(serial_number=sn)
    assert acceptance["accepted"] is True
    ac = mfg.lifecycle.register_aircraft(serial_number=sn, model="X450")
    mfg.lifecycle.add_flight_hours(ac["aircraft_id"], 1.5)
    mfg.lifecycle.add_battery_cycles(ac["aircraft_id"], 3)
    mfg.lifecycle.add_event(ac["aircraft_id"], bucket="firmware", event={"version": "4.5.0"})
    updated = mfg.lifecycle.get(ac["aircraft_id"])
    assert updated["flight_hours"] == 1.5
    assert updated["battery_cycles"] == 3
    eol = mfg.lifecycle.end_of_life(ac["aircraft_id"], reason="demo")
    assert eol["status"] == "end_of_life"


def test_warehouse_categories_and_traceability():
    mfg = drone_platform.manufacturing_suite
    assert "motors" in mfg.warehouse.categories()
    wh = drone_platform.inventory.create_warehouse(name="WH2")
    drone_platform.inventory.create_supplier(name="PartsCo")
    stock = mfg.warehouse.receive_components(
        warehouse_id=wh.warehouse_id,
        component_type="flight_controllers",
        sku="FC-1",
        quantity=1,
        serial_numbers=["FC-SN-1"],
    )
    assert stock["sku"] == "FC-1"
    trace = mfg.warehouse.traceability(serial_number="FC-SN-1")
    assert trace["found"] is True
    levels = mfg.warehouse.stock_levels(warehouse_id=wh.warehouse_id)
    assert levels["levels"]["FC-1"] == 1


def test_production_ai():
    caps = drone_platform.ai.capabilities()
    assert "detect_assembly_mistakes" in caps
    assert "estimate_manufacturing_cost" in caps
    mistakes = drone_platform.ai.assist(agent="detect_assembly_mistakes", query="x", context={"observations": ["wrong torque", "missing nut"]})
    assert mistakes["agent"] == "detect_assembly_mistakes"
    cost = drone_platform.ai.estimate_manufacturing_cost(bom_cost=200, labor_hours=5)
    assert cost["response"]["total_cost"] > 200


@pytest.mark.asyncio
async def test_api_manufacturing(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "1.8.0-alpha"
    assert body["drone_manufacturing_ready"] is True

    status = await client.get(f"{PREFIX}/manufacturing/suite")
    assert status.status == 200
    assert (await status.json())["ready"] is True

    order = await client.post(f"{PREFIX}/manufacturing/orders", json={"product_name": "Hex", "quantity": 1})
    assert order.status == 201
    order_body = await order.json()

    tmpl = await client.post(f"{PREFIX}/manufacturing/assembly", json={"action": "template", "name": "T1"})
    assert tmpl.status == 201
    tmpl_body = await tmpl.json()
    asm = await client.post(
        f"{PREFIX}/manufacturing/assembly",
        json={"order_id": order_body["order_id"], "template_id": tmpl_body["template_id"]},
    )
    assert asm.status == 201

    bom = await client.post(
        f"{PREFIX}/manufacturing/bom",
        json={"name": "B1", "lines": [{"sku": "X", "qty": 1, "unit_cost": 10}]},
    )
    assert bom.status == 201

    wh = await client.post(f"{PREFIX}/inventory/warehouses", json={"name": "API-WH"})
    wh_body = await wh.json()
    recv = await client.post(
        f"{PREFIX}/manufacturing/warehouse",
        json={"warehouse_id": wh_body["warehouse_id"], "component_type": "propellers", "sku": "P15", "quantity": 4},
    )
    assert recv.status == 201

    life = await client.post(f"{PREFIX}/manufacturing/lifecycle", json={"serial_number": "SN-API-1", "model": "X"})
    assert life.status == 201


def test_docs_and_knowledge_11_6():
    for name in ("MANUFACTURING.md", "ASSEMBLY.md", "QUALITY_CONTROL.md", "PRODUCTION_WORKFLOW.md", "LIFECYCLE.md"):
        assert (ROOT / "docs" / name).exists()
    for name in (
        "MANUFACTURING_REGISTRY.md",
        "WAREHOUSE_REGISTRY.md",
        "BOM_REGISTRY.md",
        "ASSEMBLY_REGISTRY.md",
        "PRODUCTION_DASHBOARD.md",
        "KNOWLEDGE_GRAPH.md",
        "DRONE_DASHBOARD.md",
    ):
        assert (ROOT / "knowledge" / "drone" / name).exists()
    manifest = (ROOT / "applications" / "drone_platform" / "manifest.json").read_text()
    assert "1.8.0-alpha" in manifest
    assert "11.9" in manifest
