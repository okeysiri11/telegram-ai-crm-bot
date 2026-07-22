"""Tests — Drone Cloud, Remote Ops & Global Command (Sprint 11.8)."""

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


def test_version_cloud_ready():
    health = drone_platform.health()
    assert health["application_version"] == "2.0.0"
    assert health["drone_cloud_ready"] is True
    assert health["remote_operations_ready"] is True
    assert health["global_command_ready"] is True
    assert health["digital_twin_ready"] is True
    assert health["enterprise_apis_ready"] is True
    assert health["drone_platform_enterprise_ready"] is True
    assert health["drone_platform_operational"] is True
    assert health["engines"]["drone_cloud"] == "1.0"
    assert health["engines"]["ai"] == "2.0"
    assert health["cloud_status"]["ready"] is True


def test_cloud_manager_sync_backup_auth():
    cloud = drone_platform.cloud
    n1 = cloud.manager.register_node(name="Edge-KY", region="eu-central", company_id="co1")
    n2 = cloud.manager.register_node(name="HQ", region="eu-central", node_type="core", company_id="co1")
    sync = cloud.manager.sync(source_id=n1["cloud_id"], target_id=n2["cloud_id"])
    assert sync["status"] == "completed"
    bak = cloud.manager.backup(cloud_id=n1["cloud_id"])
    assert bak["backup_id"]
    obj = cloud.manager.store_object(key="missions/a.json", content='{"ok":true}', cloud_id=n1["cloud_id"])
    assert obj["size_bytes"] > 0
    auth = cloud.manager.authenticate(principal="ops@example.com", role="supervisor")
    assert auth["authenticated"] is True
    audit = cloud.manager.audit(actor="ops@example.com", action="login", resource="cloud")
    assert audit["audit_id"]
    assert cloud.manager.gateway_route(path="/missions")["routed"] is True


def test_remote_ops_and_fleet_cloud():
    cloud = drone_platform.cloud
    session = cloud.remote.open_session(operator_id="op1", aircraft_id="ac1")
    assert session["status"] == "active"
    assert cloud.remote.remote_mission_control(session["remote_session_id"], command="ARM")["accepted"] is True
    assert cloud.remote.remote_ground_station(session["remote_session_id"])["type"] == "remote_gcs"
    assert cloud.remote.remote_firmware_upload(session["remote_session_id"], firmware_id="fw1")["status"] == "queued"
    assert cloud.remote.remote_parameter_edit(session["remote_session_id"], parameters={"RTL_ALT": 50})["count"] == 1
    assert cloud.remote.remote_mission_upload(session["remote_session_id"], waypoints=[{"lat": 1, "lon": 2}])["waypoint_count"] == 1
    assert cloud.remote.remote_log_download(session["remote_session_id"])["status"] == "ready"
    assert cloud.remote.remote_diagnostics(session["remote_session_id"])["health_score"] > 0.5
    assert cloud.remote.remote_camera_stream(session["remote_session_id"])["camera_stream"] is True
    assert cloud.remote.remote_telemetry(session["remote_session_id"])["telemetry"] is True
    assert cloud.remote.remote_shell(session["remote_session_id"], command="uname")["exit_code"] == 0

    f1 = cloud.fleet.register_org_fleet(name="Fleet A", company_id="co1", country="UA")
    f2 = cloud.fleet.register_org_fleet(name="Fleet B", company_id="co2", country="PL")
    cloud.fleet.share_fleet(f1["cloud_fleet_id"], with_company_id="co2")
    cloud.fleet.federate(f1["cloud_fleet_id"], peer_fleet_id=f2["cloud_fleet_id"])
    dash = cloud.fleet.global_dashboard()
    assert dash["fleet_count"] == 2
    assert "UA" in dash["countries"]
    asg = cloud.fleet.remote_assignment(f1["cloud_fleet_id"], operator_id="op1", mission_id="m1")
    assert asg["status"] == "assigned"
    cloud.fleet.remote_maintenance(f2["cloud_fleet_id"], notes="motor swap")


def test_global_command_twins_security_enterprise():
    cloud = drone_platform.cloud
    assert cloud.command.operations_center()["center"] == "global_command"
    track = cloud.command.live_track(aircraft_id="ac1", lat=50.45, lon=30.52, alt=40)
    assert track["lat"] == 50.45
    assert cloud.command.live_aircraft_tracking()["count"] == 1
    inc = cloud.command.raise_incident(title="Link degrade", severity="high", aircraft_id="ac1")
    assert inc["status"] == "open"
    assert cloud.command.incident_dashboard()["count"] == 1

    twin = cloud.twins.aircraft_twin(name="UAV-1 Twin", aircraft_id="ac1")
    synced = cloud.twins.live_sync(twin["twin_id"], state={"battery_pct": 72})
    assert synced["synced"] is True
    assert synced["state"]["battery_pct"] == 72
    assert cloud.twins.battery_twin(name="Pack A")["twin_type"] == "battery"

    assert cloud.security.encrypt_telemetry(payload="pos=1")["encrypted"] is True
    assert cloud.security.encrypt_command(command="RTL")["encrypted"] is True
    cert = cloud.security.issue_certificate(subject="op1", purpose="operator")
    assert cert["status"] == "active"
    cloud.security.grant_role(principal="op1", role="mission_commander")
    cloud.security.operator_permissions(operator_id="op1", permissions=["view_mission", "command"])
    cloud.security.mission_permissions(mission_id="m1", principal="op1", permissions=["read", "edit"])
    cloud.security.audit_log(actor="op1", action="command", resource="ac1")

    assert "mqtt" in cloud.enterprise.supported()
    assert cloud.enterprise.connect(protocol="ros2")["connected"] is True
    assert cloud.enterprise.connect(protocol="qgroundcontrol")["connected"] is True
    assert cloud.visualization.global_live_map(tracks=[track])["type"] == "global_live_map"

    build = cloud.remote_eng.remote_firmware_build(board="Pixhawk")
    assert build["kind"] == "firmware_build"


def test_cloud_ai_command_center():
    caps = drone_platform.ai.capabilities()
    assert "predict_failures" in caps
    assert "monitor_all_aircraft" in caps
    mon = drone_platform.ai.assist(agent="monitor_all_aircraft", query="scan", context={"aircraft": [{"id": "a1", "health": 0.5}]})
    assert mon["agent"] == "monitor_all_aircraft"
    fail = drone_platform.ai.assist(agent="predict_failures", query="x", context={"vibration": 0.9, "esc_temp_c": 90})
    assert fail["response"]["failure_risk"] == "high"
    batt = drone_platform.ai.assist(agent="recommend_battery_replacements", query="b", context={"soh": 0.7, "cycles": 210})
    assert batt["response"]["replace"] is True


@pytest.mark.asyncio
async def test_api_cloud(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "2.0.0"
    assert body["drone_platform_enterprise_ready"] is True

    status = await client.get(f"{PREFIX}/cloud")
    assert status.status == 200
    assert (await status.json())["ready"] is True

    node = await client.post(f"{PREFIX}/cloud/nodes", json={"name": "N1", "company_id": "c1"})
    assert node.status == 201
    n1 = await node.json()
    n2 = await (await client.post(f"{PREFIX}/cloud/nodes", json={"name": "N2", "company_id": "c1"})).json()
    sync = await client.post(f"{PREFIX}/cloud/sync", json={"source_id": n1["cloud_id"], "target_id": n2["cloud_id"]})
    assert sync.status == 201

    remote = await client.post(f"{PREFIX}/cloud/remote", json={"operator_id": "op1", "aircraft_id": "ac1"})
    assert remote.status == 201
    sid = (await remote.json())["remote_session_id"]
    cmd = await client.post(f"{PREFIX}/cloud/remote", json={"action": "command", "remote_session_id": sid, "command": "RTL"})
    assert cmd.status == 200

    fleet = await client.post(f"{PREFIX}/cloud/fleet", json={"name": "F1", "company_id": "co1", "country": "UA"})
    assert fleet.status == 201

    track = await client.post(f"{PREFIX}/cloud/command", json={"aircraft_id": "ac1", "lat": 50.4, "lon": 30.5})
    assert track.status == 201

    twin = await client.post(f"{PREFIX}/cloud/twins", json={"twin_type": "aircraft", "name": "T1", "source_id": "ac1"})
    assert twin.status == 201

    sec = await client.post(f"{PREFIX}/cloud/security", json={"action": "certificate", "subject": "op1"})
    assert sec.status == 201

    ent = await client.get(f"{PREFIX}/cloud/enterprise")
    assert ent.status == 200
    assert "rest" in await ent.json()


def test_docs_and_knowledge_11_8():
    for name in ("CLOUD.md", "REMOTE_OPERATIONS.md", "GLOBAL_COMMAND.md", "DIGITAL_TWIN.md", "ENTERPRISE_APIS.md"):
        assert (ROOT / "docs" / name).exists()
    for name in (
        "CLOUD_REGISTRY.md",
        "CLOUD_DASHBOARD.md",
        "FLEET_REGISTRY.md",
        "MISSION_REGISTRY.md",
        "ENGINEERING_REGISTRY.md",
        "KNOWLEDGE_GRAPH.md",
        "DRONE_DASHBOARD.md",
    ):
        assert (ROOT / "knowledge" / "drone" / name).exists()
    manifest = (ROOT / "applications" / "drone_platform" / "manifest.json").read_text()
    assert "2.0.0" in manifest
    assert "11.10" in manifest
