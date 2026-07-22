"""Tests — Drone Platform Foundation (Sprint 11.1)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.drone_platform import drone_platform
from applications.drone_platform.api.register import register_drone_platform_routes
from applications.drone_platform.models.components import COMPONENT_TYPES
from applications.drone_platform.models.firmware import FIRMWARE_STACKS


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


def test_version_and_foundation_ready():
    health = drone_platform.health()
    assert health["application"] == "drone_platform"
    assert health["application_name"] == "Drone Platform"
    assert health["application_version"] == "1.1.0-alpha"
    assert health["foundation_ready"] is True
    assert health["engineering_ready"] is True
    assert health["firmware_workspace_ready"] is True
    assert health["mission_planning_ready"] is True
    assert health["inventory_ready"] is True
    assert health["ai_engineering_assistant_ready"] is True
    assert health["api_prefix"] == PREFIX


def test_docs_and_manifest():
    assert (ROOT / "docs" / "DRONE_PLATFORM.md").exists()
    manifest = ROOT / "applications" / "drone_platform" / "manifest.json"
    assert manifest.exists()
    text = manifest.read_text()
    assert "1.1.0-alpha" in text
    assert "11.2" in text


def test_package_layout():
    base = ROOT / "applications" / "drone_platform"
    for name in (
        "api",
        "models",
        "registry",
        "projects",
        "engineering",
        "firmware",
        "missions",
        "telemetry",
        "inventory",
        "warehouse",
        "manufacturing",
        "simulation",
        "ai",
        "documentation",
        "integrations",
        "analytics",
        "shared",
    ):
        assert (base / name).is_dir()


def test_forbidden_apps_untouched():
    # Sprint constraint: only drone_platform app code; siblings must remain untouched by this sprint.
    for forbidden in (
        "applications/auto_marketplace",
        "applications/agro_marketplace",
        "applications/port_erp",
        "ecosystem",
    ):
        path = ROOT / forbidden
        assert path.exists()
    # Bridges exist inside drone_platform only
    integrations = ROOT / "applications" / "drone_platform" / "integrations"
    assert (integrations / "platform_bridge.py").exists()
    assert (integrations / "ecosystem_bridge.py").exists()


def test_registry_components_and_uavs():
    types = drone_platform.registry.list_component_types()
    assert "motor" in types
    assert "flight_controller" in types
    assert "companion_computer" in types
    assert len(types) == len(COMPONENT_TYPES)

    motor = drone_platform.registry.register_component(
        component_type="motor",
        name="T-Motor MN4014",
        manufacturer="T-Motor",
        model="MN4014",
        specifications={"kv": 400},
    )
    fc = drone_platform.registry.register_component(
        component_type="flight_controller",
        name="Cube Orange",
        manufacturer="CubePilot",
    )
    uav = drone_platform.registry.register_uav(
        name="Dev Quad X",
        airframe_type="multirotor",
        flight_controller_id=fc.component_id,
        component_ids=[motor.component_id, fc.component_id],
    )
    assert uav.uav_id
    summary = drone_platform.registry.catalog_summary()
    assert summary["component_count"] >= 2
    assert summary["uav_count"] == 1


def test_engineering_projects():
    project = drone_platform.projects.create_project(name="Heavy Lift Frame", owner="eng-1")
    version = drone_platform.projects.create_version(
        project_id=project.project_id,
        version="0.1.0",
        bom=[{"sku": "MOT-4014", "qty": 4}],
        cad_references=[{"path": "cad/frame.step"}],
        pcb_references=[{"path": "pcb/power.pdf"}],
        wiring_diagrams=[{"path": "wiring/main.svg"}],
        assembly_instructions=["Mount motors", "Route power"],
        engineering_notes=["Initial prototype"],
    )
    assert version.bom[0]["sku"] == "MOT-4014"
    workspace = drone_platform.engineering.workspace_summary(project.project_id)
    assert workspace["version_count"] == 1
    assert "bom" in workspace["capabilities"]


def test_firmware_workspace():
    assert set(drone_platform.firmware.supported_stacks()) == set(FIRMWARE_STACKS)
    fw = drone_platform.firmware.create_project(name="Dev Copter", stack="ArduPilot", version="4.5.0")
    assert fw.stack == "ardupilot"
    left = drone_platform.firmware.save_parameters(
        firmware_project_id=fw.firmware_project_id,
        name="baseline",
        parameters={"ATC_RAT_PIT_P": 0.1, "BATT_CAPACITY": 5000},
    )
    right = drone_platform.firmware.save_parameters(
        firmware_project_id=fw.firmware_project_id,
        name="tuned",
        parameters={"ATC_RAT_PIT_P": 0.12, "BATT_CAPACITY": 5000, "FENCE_ENABLE": 1},
    )
    diff = drone_platform.firmware.compare_parameters(left.parameter_set_id, right.parameter_set_id)
    assert any(c["parameter"] == "ATC_RAT_PIT_P" for c in diff["changed"])
    assert "FENCE_ENABLE" in diff["only_right"]

    backup_params = drone_platform.firmware.backup_parameters(left.parameter_set_id, label="safe")
    restored = drone_platform.firmware.restore_parameters(backup_params.parameter_set_id, target_name="restored")
    assert restored.parameters["BATT_CAPACITY"] == 5000

    template = drone_platform.firmware.create_template(
        name="quad-default",
        stack="px4",
        parameters={"MPC_XY_VEL_MAX": 12},
    )
    assert template.stack == "px4"

    exported = drone_platform.firmware.export_configuration(left.parameter_set_id)
    imported = drone_platform.firmware.import_configuration(
        firmware_project_id=fw.firmware_project_id,
        name="from-export",
        payload=exported,
    )
    assert imported.parameters["ATC_RAT_PIT_P"] == 0.1

    fw_backup = drone_platform.firmware.backup_firmware(
        firmware_project_id=fw.firmware_project_id,
        label="pre-upgrade",
        payload={"version": "4.5.0", "stack": "ardupilot"},
    )
    fw.version = "4.6.0"
    drone_platform.store.firmware_projects.save(fw.firmware_project_id, fw)
    restored_fw = drone_platform.firmware.restore_firmware(fw_backup.backup_id)
    assert restored_fw.version == "4.5.0"

    drone_platform.firmware.organize_logs(fw.firmware_project_id, ["logs/flight1.bin"])
    drone_platform.firmware.update_documentation(fw.firmware_project_id, "Bench tune notes")
    catalog = drone_platform.firmware.catalog()
    assert catalog["projects_by_stack"]["ardupilot"]


def test_mission_planning():
    mission = drone_platform.missions.create_mission(
        name="Survey A",
        waypoints=[{"sequence": 1, "latitude": 1.0, "longitude": 36.0, "altitude_m": 50}],
        rally_points=[{"latitude": 1.01, "longitude": 36.01, "altitude_m": 40}],
        geofences=[{"name": "pad", "vertices": [{"lat": 1.0, "lon": 36.0}], "max_altitude_m": 120}],
        payload_configuration={"camera": "mapping"},
        flight_profile={"name": "survey", "cruise_speed_mps": 8},
    )
    mission = drone_platform.missions.add_waypoint(
        mission.mission_id,
        {"latitude": 1.02, "longitude": 36.02, "altitude_m": 55},
    )
    assert len(mission.waypoints) == 2
    template = drone_platform.missions.clone_as_template(mission.mission_id, "Survey Template")
    assert template.is_template is True
    assert len(drone_platform.missions.list_missions(templates_only=True)) == 1


def test_inventory_flow():
    wh = drone_platform.inventory.create_warehouse(name="Main Bay", location="Hangar 1")
    supplier = drone_platform.inventory.create_supplier(name="UAV Parts Co", contact="parts@example.com")
    stock = drone_platform.inventory.add_stock(
        warehouse_id=wh.warehouse_id,
        component_type="motor",
        sku="MOT-4014",
        quantity=10,
        serial_numbers=["SN1", "SN2"],
        batch_id="BATCH-1",
    )
    reservation = drone_platform.inventory.reserve_stock(
        stock_id=stock.stock_id,
        quantity=2,
        project_id="prj_demo",
    )
    assert reservation.quantity == 2
    updated = drone_platform.inventory.get_stock(stock.stock_id)
    assert updated.reserved == 2
    assert updated.to_dict()["available"] == 8
    po = drone_platform.inventory.create_purchase_order(
        supplier_id=supplier.supplier_id,
        warehouse_id=wh.warehouse_id,
        lines=[{"sku": "MOT-4014", "qty": 20}],
    )
    assert po.status == "ordered"
    drone_platform.inventory.update_lifecycle(stock.stock_id, "in_use")
    assert drone_platform.inventory.get_stock(stock.stock_id).lifecycle_stage == "in_use"


def test_documentation_and_ai():
    doc = drone_platform.documentation.create(
        title="Assembly Guide",
        doc_type="assembly_guide",
        content="Mount FC with vibration dampers.",
        tags=["assembly"],
    )
    assert doc.document_id
    caps = drone_platform.ai.capabilities()
    assert "firmware_analysis" in caps
    assert "diagnostics" in caps
    session = drone_platform.ai.assist(
        agent="parameter_explanation",
        query="ATC_RAT_PIT_P",
        context={"stack": "ardupilot", "value": 0.12},
    )
    assert session["agent"] == "parameter_explanation"
    assert session["policy"] == "engineering_assistance_only"
    review = drone_platform.ai.review_configuration(parameters={"FOO": 1, "BAR": 2}, stack="px4")
    assert review["response"]["parameter_count"] == 2


@pytest.mark.asyncio
async def test_api_health_registry_firmware_missions(client: TestClient):
    health = await client.get(f"{PREFIX}/health")
    assert health.status == 200
    body = await health.json()
    assert body["application_version"] == "1.1.0-alpha"

    types = await client.get(f"{PREFIX}/registry/types")
    assert types.status == 200
    assert "motor" in (await types.json())["component_types"]

    created = await client.post(
        f"{PREFIX}/registry/components",
        json={"component_type": "gps", "name": "Here3", "manufacturer": "CubePilot"},
    )
    assert created.status == 201

    uav = await client.post(f"{PREFIX}/registry/uavs", json={"name": "API Quad"})
    assert uav.status == 201

    project = await client.post(f"{PREFIX}/projects", json={"name": "API Project"})
    assert project.status == 201
    project_id = (await project.json())["project_id"]
    version = await client.post(
        f"{PREFIX}/projects/{project_id}/versions",
        json={"version": "0.1.0", "bom": [{"sku": "FC-1", "qty": 1}]},
    )
    assert version.status == 201

    eng = await client.get(f"{PREFIX}/engineering/{project_id}")
    assert eng.status == 200

    fw = await client.post(
        f"{PREFIX}/firmware/projects",
        json={"name": "BF Tune", "stack": "betaflight", "version": "4.4"},
    )
    assert fw.status == 201
    fw_id = (await fw.json())["firmware_project_id"]
    params = await client.post(
        f"{PREFIX}/firmware/parameters",
        json={"firmware_project_id": fw_id, "name": "p1", "parameters": {"gyro_lpf": 2}},
    )
    assert params.status == 201

    mission = await client.post(
        f"{PREFIX}/missions",
        json={"name": "API Mission", "waypoints": [{"latitude": 0, "longitude": 0, "altitude_m": 30}]},
    )
    assert mission.status == 201
    mission_id = (await mission.json())["mission_id"]
    wp = await client.post(
        f"{PREFIX}/missions/{mission_id}/waypoints",
        json={"latitude": 0.1, "longitude": 0.1, "altitude_m": 40},
    )
    assert wp.status == 200

    wh = await client.post(f"{PREFIX}/inventory/warehouses", json={"name": "Bay"})
    assert wh.status == 201
    wh_id = (await wh.json())["warehouse_id"]
    stock = await client.post(
        f"{PREFIX}/inventory/stock",
        json={"warehouse_id": wh_id, "component_type": "battery", "sku": "BAT-6S", "quantity": 5},
    )
    assert stock.status == 201

    docs = await client.post(
        f"{PREFIX}/documentation",
        json={"title": "Manual", "doc_type": "manual", "content": "Ops"},
    )
    assert docs.status == 201

    ai = await client.post(
        f"{PREFIX}/ai/assist",
        json={"agent": "troubleshooting", "query": "ESC desync on spoolup", "context": {}},
    )
    assert ai.status == 200
    ai_body = await ai.json()
    assert ai_body["agent"] == "troubleshooting"
