"""Tests — Drone Ecosystem Completion & Enterprise Platform Validation (Sprint 31.4)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.drone_platform import drone_platform
from applications.drone_platform.api.register import register_drone_platform_routes


ROOT = Path(__file__).resolve().parents[1]
DRONE = "/api/drone/v1"

DOCS = [
    "DRONE_PILOT_EXECUTION_31_4.md",
    "DRONE_INTEGRATION_31_4.md",
    "MISSION_WORKFLOW_31_4.md",
    "PRODUCTION_GUIDE_31_4.md",
    "ECOSYSTEM_REUSE_MATRIX_31_4.md",
    "ENTERPRISE_READINESS_MATRIX_31_4.md",
    "ARCHITECTURE_INVENTORY_31_4.md",
    "RELEASE_NOTES_31_4.md",
    "SPRINT_REPORT_31_4.md",
]


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
    platform_builder.reset()
    drone_platform.reset()
    yield
    platform_builder.reset()
    drone_platform.reset()


def test_drone_docs_exist():
    docs = ROOT / "docs"
    for name in DOCS:
        path = docs / name
        assert path.exists(), name
        assert "31.4" in path.read_text()


def test_platform_drone_version():
    health = platform_builder.health()
    assert health["application_version"] == "1.60.0"
    assert health["sprint"] == "33.4"
    assert health["release_status"] == "Predictive Intelligence & Scenario Simulator"


@pytest.mark.asyncio
async def test_drone_production_and_mission_api(client):
    health = await client.get(f"{DRONE}/health")
    assert health.status == 200
    body = await health.json()
    assert body.get("application_version") == "2.0.0"

    boot = await client.post(f"{DRONE}/ecosystem/bootstrap", json={})
    assert boot.status == 201

    project = await client.post(f"{DRONE}/projects", json={"name": "Pilot Project"})
    assert project.status == 201
    project_body = await project.json()
    project_id = project_body["project_id"]

    version = await client.post(
        f"{DRONE}/projects/{project_id}/versions",
        json={"version": "0.1.0", "bom": [{"sku": "FC-1", "qty": 1}]},
    )
    assert version.status == 201

    uav = await client.post(f"{DRONE}/registry/uavs", json={"name": "Pilot Quad"})
    assert uav.status == 201
    uav_body = await uav.json()

    fleet = await client.post(f"{DRONE}/ops/fleet", json={"name": "F1", "model": "X450"})
    assert fleet.status == 201

    order = await client.post(
        f"{DRONE}/manufacturing/orders",
        json={"product_name": "Hex", "quantity": 1, "project_id": project_id},
    )
    assert order.status == 201
    order_body = await order.json()

    template = await client.post(
        f"{DRONE}/manufacturing/assembly",
        json={"action": "template", "name": "T1"},
    )
    assert template.status == 201
    template_body = await template.json()

    assembly = await client.post(
        f"{DRONE}/manufacturing/assembly",
        json={"order_id": order_body["order_id"], "template_id": template_body["template_id"]},
    )
    assert assembly.status == 201

    warehouse = await client.post(f"{DRONE}/inventory/warehouses", json={"name": "Pilot-WH"})
    assert warehouse.status == 201
    warehouse_body = await warehouse.json()

    stock = await client.post(
        f"{DRONE}/inventory/stock",
        json={
            "warehouse_id": warehouse_body["warehouse_id"],
            "component_type": "battery",
            "sku": "BAT-6S",
            "quantity": 5,
        },
    )
    assert stock.status == 201

    serial = "SN-PILOT-314"
    programming = await client.post(
        f"{DRONE}/manufacturing/programming",
        json={"serial_number": serial, "firmware_version": "4.5.0", "stack": "ardupilot"},
    )
    assert programming.status == 201

    qa = await client.post(f"{DRONE}/manufacturing/qa", json={"serial_number": serial})
    assert qa.status == 201

    flight = await client.post(
        f"{DRONE}/manufacturing/flight-tests",
        json={"serial_number": serial, "test_type": "bench", "result": "pass"},
    )
    assert flight.status == 201

    mission = await client.post(
        f"{DRONE}/ops/missions",
        json={
            "name": "Pilot Mission",
            "waypoints": [{"lat": 50.45, "lon": 30.52}, {"lat": 50.46, "lon": 30.53}],
        },
    )
    assert mission.status == 201
    mission_body = await mission.json()
    ops_id = mission_body["ops_mission_id"]

    validate = await client.post(
        f"{DRONE}/ops/missions",
        json={"action": "validate", "ops_mission_id": ops_id},
    )
    assert validate.status == 200

    ground = await client.post(f"{DRONE}/ops/ground", json={"operator_id": "eng1"})
    assert ground.status == 201

    tel = await client.post(
        f"{DRONE}/telemetry/sessions",
        json={"uav_id": uav_body["uav_id"]},
    )
    assert tel.status == 201
    tel_body = await tel.json()

    sample = await client.post(
        f"{DRONE}/telemetry/sessions/{tel_body['session_id']}/samples",
        json={"battery": 90, "gps_fix": 12, "lat": 50.45, "lon": 30.52, "alt": 30, "rssi": 75},
    )
    assert sample.status in (200, 201)

    analytics = await client.post(
        f"{DRONE}/ops/analytics",
        json={"kind": "success_rate", "reports": [{"success": True}, {"success": False}]},
    )
    assert analytics.status == 201

    assert (await client.get(f"{DRONE}/ecosystem/dashboard")).status == 200
    assert (await client.post(f"{DRONE}/ecosystem/reports", json={"report_type": "executive"})).status == 201


def test_all_seven_pilot_routes_present():
    web = ROOT / "src" / "web"
    app = (web / "src" / "App.tsx").read_text()
    for needle in (
        'path="/workspace/auto"',
        "AutomotiveLiveWorkflowPage",
        'path="/workspace/beauty"',
        "BeautyLiveWorkflowPage",
        'path="/workspace/cafe"',
        "CafeLiveWorkflowPage",
        'path="/workspace/agro"',
        "AgricultureLiveWorkflowPage",
        'path="/workspace/legal"',
        "LegalLiveWorkflowPage",
        'path="/workspace/crypto"',
        "BidexLiveWorkflowPage",
        'path="/workspace/drone"',
        "DroneLiveWorkflowPage",
    ):
        assert needle in app, needle
    assert (web / "workspace" / "drone" / "droneWorkflow.ts").exists()


def test_drone_web_and_reuse_matrix():
    web = ROOT / "src" / "web"
    wf = (web / "workspace" / "drone" / "droneWorkflow.ts").read_text()
    for needle in (
        "project",
        "aircraft",
        "assembly",
        "testing",
        "mission_planning",
        "drone_mission_control",
        "stepAiTeamConfigure",
        "quality_gates",
        "runDroneLiveWorkflow",
        "dronePrefix",
        "precisionAgriculturePrefix",
    ):
        assert needle in wf, needle
    cfg = (web / "src" / "config" / "webConfig.ts").read_text()
    assert 'sprint: "33.4"' in cfg
    assert "dronePrefix" in cfg
    tmpl = (web / "workspace" / "ecosystem-template" / "index.ts").read_text()
    assert "drone: true" in tmpl
    assert "allSeven" in tmpl
    hub = (web / "src" / "integrations" / "hub.ts").read_text()
    assert "drone:" in hub or "drone =" in hub or "drone:" in hub
    assert "precisionAgriculture" in hub


def test_reuse_docs_and_manifest():
    text = (ROOT / "docs" / "ECOSYSTEM_REUSE_MATRIX_31_4.md").read_text()
    assert "100%" in text
    assert "Drone" in text
    readiness = (ROOT / "docs" / "ENTERPRISE_READINESS_MATRIX_31_4.md").read_text()
    assert "complete" in readiness.lower() or "COMPLETE" in readiness
    for eco in ("Automotive", "Beauty", "Cafe", "Agriculture", "Legal", "Bidex", "Drone"):
        assert eco in readiness
    report = (ROOT / "docs" / "SPRINT_REPORT_31_4.md").read_text()
    assert "COMPLETE" in report
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.60.0"' in manifest
    assert "33.4" in manifest
    assert "Predictive Intelligence & Scenario Simulator" in manifest
    index = (ROOT / "docs" / "ARCHITECTURE_AUDIT_INDEX.md").read_text()
    assert "DRONE_PILOT_EXECUTION_31_4" in index
