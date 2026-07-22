"""Tests — Mission Operations, Fleet & Swarm (Sprint 11.7)."""

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


def test_version_mission_ops_ready():
    health = drone_platform.health()
    assert health["application_version"] == "2.0.0"
    assert health["mission_operations_ready"] is True
    assert health["fleet_command_ready"] is True
    assert health["ground_control_ready"] is True
    assert health["swarm_intelligence_ready"] is True
    assert health["mission_ai_ready"] is True
    assert health["drone_platform_operational"] is True
    assert health["engines"]["mission_operations"] == "1.0"
    assert health["engines"]["ai"] == "2.0"


def test_mission_center_flow():
    ops = drone_platform.mission_ops
    mission = ops.center.create_ops_mission(
        name="Survey A",
        waypoints=[{"lat": 50.45, "lon": 30.52, "alt": 50}, {"lat": 50.46, "lon": 30.53, "alt": 55}],
        priority="high",
    )
    assert mission["status"] == "draft"
    assert ops.center.validate(mission["ops_mission_id"])["valid"] is True
    ops.center.schedule(mission["ops_mission_id"], scheduled_at="2026-07-22T10:00:00Z")
    assert ops.center.simulate(mission["ops_mission_id"])["status"] == "simulated"
    assert ops.center.replay(mission["ops_mission_id"])["step_count"] == 2
    assert ops.center.timeline(mission["ops_mission_id"])["events"]
    report = ops.center.report(mission["ops_mission_id"], success=True)
    assert report["success"] is True
    archive = ops.center.archive(mission["ops_mission_id"])
    assert archive["archive_id"]
    tmpl = ops.center.create_template(name="Grid", waypoints=[{"lat": 1, "lon": 2}])
    assert tmpl["is_template"] is True


def test_fleet_ground_swarm_emergency():
    ops = drone_platform.mission_ops
    a1 = ops.fleet.register_aircraft(name="UAV-1", model="X450")
    a2 = ops.fleet.register_aircraft(name="UAV-2", model="X450")
    assert ops.fleet.readiness(a1["fleet_id"])["ready"] is True
    asg = ops.fleet.assign(a1["fleet_id"], pilot_id="pilot1", battery_id="bat1", equipment=["cam"])
    assert asg["pilot_id"] == "pilot1"
    session = ops.ground.open_session(operator_id="op1", role="mission_commander")
    alert = ops.ground.raise_alert(severity="warning", message="Wind rising", ops_mission_id="ops_x")
    assert alert["status"] == "open"
    assert ops.ground.operator_console(session["session_id"])["console"] == "operator"
    swarm = ops.swarm.create_swarm_mission(name="Sweep", fleet_ids=[a1["fleet_id"], a2["fleet_id"]], formation="vee")
    ops.swarm.distribute_tasks(swarm["swarm_id"], tasks=[{"task": "scan"}, {"task": "relay"}])
    ops.swarm.area_coverage(swarm["swarm_id"], bounds={"south": 50.45, "north": 50.46, "west": 30.52, "east": 30.53})
    recovered = ops.swarm.automatic_recovery(swarm["swarm_id"], failed_fleet_id=a2["fleet_id"])
    assert recovered["status"] == "recovered"
    decision = ops.swarm.decision_engine(swarm["swarm_id"], observations={"coverage_gap": True})
    assert decision["primary"]["action"] == "redistribute_tasks"
    emg = ops.emergency.trigger(emergency_type="battery_critical", fleet_id=a1["fleet_id"])
    assert "rtl" in emg["actions"] or "land_nearest" in emg["actions"]
    ops.emergency.automatic_recovery(emg["emergency_id"])
    rth = ops.emergency.return_to_home(
        fleet_id=a1["fleet_id"],
        home={"lat": 50.45, "lon": 30.52},
        current={"lat": 50.451, "lon": 30.521},
        battery_pct=40,
    )
    assert rth["action"] in {"rtl", "land_immediate"}


def test_analytics_collaboration_ai_integrations():
    ops = drone_platform.mission_ops
    rate = ops.analytics.mission_success_rate(reports=[{"success": True}, {"success": False}, {"success": True}])
    assert rate["rate"] == pytest.approx(0.667, rel=1e-2)
    assert ops.analytics.coverage_analysis(planned_area_km2=2, covered_area_km2=1.5)["coverage_ratio"] == 0.75
    op = ops.collaboration.register_operator(name="Alice", role="supervisor")
    mission = ops.center.create_ops_mission(name="C", waypoints=[{"lat": 1, "lon": 2}])
    ops.collaboration.add_comment(ops_mission_id=mission["ops_mission_id"], operator_id=op["operator_id"], text="Looks good")
    apr = ops.collaboration.request_approval(ops_mission_id=mission["ops_mission_id"], requester_id=op["operator_id"])
    decided = ops.collaboration.decide_approval(apr["approval_id"], approver_id=op["operator_id"], approved=True)
    assert decided["status"] == "approved"
    assert "mission_planner" in ops.integrations.supported()
    assert ops.integrations.connect(system="ros2")["connected"] is True
    assert ops.visualization.swarm_visualization(swarm={"swarm_id": "s1", "formation": "line", "roles": [], "fleet_ids": []})["type"] == "swarm_visualization"
    caps = drone_platform.ai.capabilities()
    assert "mission_optimization" in caps
    assert "risk_prediction" in caps
    score = drone_platform.ai.assist(agent="mission_scoring", query="score", context={"validation_ok": True, "risk_level": "low", "battery_ok": True})
    assert score["agent"] == "mission_scoring"


@pytest.mark.asyncio
async def test_api_mission_ops(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "2.0.0"
    assert body["drone_platform_operational"] is True

    status = await client.get(f"{PREFIX}/ops")
    assert status.status == 200
    assert (await status.json())["ready"] is True

    mission = await client.post(
        f"{PREFIX}/ops/missions",
        json={"name": "API Mission", "waypoints": [{"lat": 50.45, "lon": 30.52}, {"lat": 50.46, "lon": 30.53}]},
    )
    assert mission.status == 201
    mid = (await mission.json())["ops_mission_id"]
    val = await client.post(f"{PREFIX}/ops/missions", json={"action": "validate", "ops_mission_id": mid})
    assert val.status == 200

    fleet = await client.post(f"{PREFIX}/ops/fleet", json={"name": "F1", "model": "X"})
    assert fleet.status == 201
    f1 = await fleet.json()
    fleet2 = await (await client.post(f"{PREFIX}/ops/fleet", json={"name": "F2"})).json()

    swarm = await client.post(
        f"{PREFIX}/ops/swarm",
        json={"name": "S1", "fleet_ids": [f1["fleet_id"], fleet2["fleet_id"]]},
    )
    assert swarm.status == 201

    emg = await client.post(f"{PREFIX}/ops/emergency", json={"emergency_type": "lost_link", "fleet_id": f1["fleet_id"]})
    assert emg.status == 201

    gnd = await client.post(f"{PREFIX}/ops/ground", json={"operator_id": "op1"})
    assert gnd.status == 201


def test_docs_and_knowledge_11_7():
    for name in ("MISSION_CENTER.md", "FLEET_COMMAND.md", "SWARM_AI.md", "GROUND_CONTROL.md", "MISSION_ANALYTICS.md"):
        assert (ROOT / "docs" / name).exists()
    for name in (
        "MISSION_OPS_REGISTRY.md",
        "FLEET_REGISTRY.md",
        "SWARM_REGISTRY.md",
        "MISSION_OPS_DASHBOARD.md",
        "MISSION_REGISTRY.md",
        "KNOWLEDGE_GRAPH.md",
        "DRONE_DASHBOARD.md",
    ):
        assert (ROOT / "knowledge" / "drone" / name).exists()
    manifest = (ROOT / "applications" / "drone_platform" / "manifest.json").read_text()
    assert "2.0.0" in manifest
    assert "11.10" in manifest
