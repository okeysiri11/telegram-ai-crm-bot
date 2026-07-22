"""Tests — MAVLink / Telemetry AI / Flight Logs (Sprint 11.3)."""

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


def test_version_mavlink_telemetry_ready():
    health = drone_platform.health()
    assert health["application_version"] == "1.7.0-alpha"
    assert health["mavlink_intelligence_ready"] is True
    assert health["telemetry_ai_ready"] is True
    assert health["flight_log_analysis_ready"] is True
    assert health["mission_intelligence_ready"] is True
    assert health["gcs_integration_ready"] is True
    assert health["drone_diagnostics_ready"] is True
    assert health["telemetry_flight_ai_ready"] is True
    assert health["engines"]["mavlink"] == "1.0"
    assert health["engines"]["ai"] == "1.7"


def test_mavlink_parse_router_heartbeat_stream():
    parsed = drone_platform.mavlink.parser.parse("HEARTBEAT type=2 autopilot=3 base_mode=81")
    assert parsed["msg_name"] == "HEARTBEAT"
    assert parsed["known"] is True
    assert any(m["name"] == "GPS_RAW_INT" for m in drone_platform.mavlink.messages.list_messages())
    assert any(c["name"] == "MAV_CMD_NAV_WAYPOINT" for c in drone_platform.mavlink.commands.list_commands())
    conn_a = drone_platform.mavlink.connections.create(name="GCS", endpoint="udpout:127.0.0.1:14550")
    conn_b = drone_platform.mavlink.connections.create(name="FC", endpoint="serial:/dev/ttyACM0")
    route = drone_platform.mavlink.router.add_route(
        source_connection_id=conn_a["connection_id"],
        target_connection_id=conn_b["connection_id"],
        message_filter=["HEARTBEAT"],
    )
    fwd = drone_platform.mavlink.router.forward(route["route_id"], parsed)
    assert fwd["forwarded"] is True
    beat = drone_platform.mavlink.heartbeat.record(system_id=1, autopilot="ardupilot", vehicle_type="quadrotor")
    vehicle = drone_platform.mavlink.discovery.discover_from_heartbeat(beat)
    assert vehicle["system_id"] == 1
    stream = drone_platform.mavlink.streams.open_stream(connection_id=conn_a["connection_id"])
    msg = drone_platform.mavlink.streams.ingest(stream["stream_id"], "ATTITUDE roll=0.1 pitch=-0.05 yaw=1.2")
    assert msg["msg_name"] == "ATTITUDE"
    assert drone_platform.mavlink.parameters.set_param(param_id="BATT_CAPACITY", value=5000)["status"] == "queued"
    assert "logs/" in drone_platform.mavlink.ftp.list_directory()["entries"][1]


def test_telemetry_ai_analyzers_record_replay():
    session = drone_platform.telemetry.start_session(uav_id="uav_1", mission_id="msn_1")
    samples = [
        {"lat": 50.45, "lon": 30.52, "alt": 40, "battery": 95, "voltage": 16.4, "gps_fix": 12, "rssi": 80, "current": 12, "motors": [1400, 1410, 1395, 1405]},
        {"lat": 50.451, "lon": 30.521, "alt": 45, "battery": 88, "voltage": 16.1, "gps_fix": 11, "rssi": 72, "current": 14, "motors": [1450, 1460, 1440, 1455]},
        {"lat": 50.452, "lon": 30.522, "alt": 50, "battery": 80, "voltage": 15.8, "gps_fix": 10, "rssi": 65, "current": 15, "rc_loss": False},
    ]
    for s in samples:
        drone_platform.telemetry.record_sample(session["session_id"], s)
    analysis = drone_platform.telemetry_ai.analyze_session(session["session_id"])
    assert analysis["sample_count"] == 3
    assert analysis["analyzers"]["battery"]["status"] == "ok"
    assert analysis["analyzers"]["gps_quality"]["quality"] in {"good", "fair", "poor"}
    recording = drone_platform.telemetry_ai.recorder.start(session["session_id"], label="demo")
    stopped = drone_platform.telemetry_ai.recorder.stop(recording["recording_id"])
    assert stopped["status"] == "stopped"
    replay = drone_platform.telemetry_ai.replay.create(session["session_id"])
    step = drone_platform.telemetry_ai.replay.step(replay["replay_id"])
    assert step["finished"] is False
    assert step["sample"]["battery"] == 95


def test_flight_log_parser_and_px4_architecture():
    content = "\n".join(
        [
            "HEARTBEAT type=2 autopilot=3",
            "STATUSTEXT text=EKF_CHECK",
            "GPS_RAW_INT fix_sat=4 lat=504500000 lon=305200000",
            "SYS_STATUS battery_remaining=12",
        ]
    )
    log = drone_platform.flight_logs.ingest(name="demo.tlog", content=content, filename="demo.tlog")
    assert log["log_type"] in {".tlog", "mavlink", "mission_planner"}
    assert log["analysis"]["message_count"] >= 1
    px4 = drone_platform.flight_logs.ingest(name="flight.ulg", content="", filename="flight.ulg", log_type="px4_ulog")
    assert px4["parsed"]["architecture_ready"] is True
    assert "px4_ulog" in drone_platform.flight_logs.supported_types()
    df = drone_platform.flight_logs.ingest(
        name="dataflash.log",
        content="PARM,BATT_CAPACITY,5000\nMSG,Failsafe triggered\n",
        filename="dataflash.log",
        log_type="ardupilot_dataflash",
    )
    assert df["parsed"]["parameters"]["BATT_CAPACITY"] == 5000


def test_diagnostics_detects_anomalies():
    samples = [
        {"gps_fix": 3, "gps_glitch": True},
        {"compass_error": True, "vibe": 40},
        {"ekf_error": True, "rc_loss": True},
        {"voltage": 8.5, "battery": 8, "crash": True},
    ]
    report = drone_platform.diagnostics.detect(samples)
    assert "gps_glitch" in report["detected_types"]
    assert "crash_indicator" in report["detected_types"]
    assert report["severity"] == "critical"


def test_mission_intelligence_and_gcs_visualization():
    mission = drone_platform.missions.create_mission(
        name="Survey",
        waypoints=[
            {"lat": 50.45, "lon": 30.52, "alt": 50},
            {"lat": 50.46, "lon": 30.53, "alt": 55},
            {"lat": 50.47, "lon": 30.54, "alt": 60},
        ],
        rally_points=[{"lat": 50.449, "lon": 30.519, "name": "rally1"}],
    )
    analysis = drone_platform.mission_intel.analyze_mission(mission.mission_id, battery_pct=90, wind_mps=3)
    assert analysis["validation"]["valid"] is True
    assert "score" in analysis
    assert analysis["battery"]["estimated_remaining_pct"] is not None
    other = drone_platform.missions.create_mission(
        name="Survey-B",
        waypoints=[{"lat": 50.45, "lon": 30.52, "alt": 40}, {"lat": 50.455, "lon": 30.525, "alt": 45}],
    )
    cmp = drone_platform.mission_intel.compare_missions(mission.mission_id, other.mission_id)
    assert cmp["waypoint_delta"] == -1
    rth = drone_platform.mission_intel.simulate_rth(
        home={"lat": 50.45, "lon": 30.52},
        current={"lat": 50.46, "lon": 30.53},
        battery_pct=70,
    )
    assert "rth_viable" in rth
    emergency = drone_platform.mission_intel.emergency_landing(mission.mission_id, {"lat": 50.451, "lon": 30.521})
    assert emergency["primary"]["distance_m"] >= 0
    bridge = drone_platform.gcs.create_bridge(name="MP", gcs_type="mission_planner", endpoint="tcp:127.0.0.1:5760")
    assert bridge["gcs_type"] == "mission_planner"
    for gcs_type in ("qgroundcontrol", "mavproxy", "apm_planner", "custom"):
        drone_platform.gcs.create_bridge(name=gcs_type, gcs_type=gcs_type)
    session = drone_platform.telemetry.start_session(uav_id="uav_1")
    drone_platform.telemetry.record_sample(session["session_id"], {"lat": 50.45, "lon": 30.52, "alt": 40, "battery": 90, "rssi": 70, "speed": 8, "current": 10})
    bundle = drone_platform.visualization.build_bundle(
        drone_platform.telemetry.get_session(session["session_id"])["samples"],
        waypoints=mission.waypoints,
        events=[{"type": "takeoff"}],
    )
    assert "gps_track" in bundle
    assert "battery_chart" in bundle


def test_telemetry_flight_ai_assist():
    caps = drone_platform.ai.capabilities()
    assert "explain_mavlink_message" in caps
    assert "diagnose_flight" in caps
    result = drone_platform.ai.assist(agent="explain_mavlink_message", query="HEARTBEAT", context={})
    assert result["agent"] == "explain_mavlink_message"
    diag = drone_platform.ai.assist(agent="diagnose_flight", query="gps", context={"detections": ["gps_glitch"]})
    assert diag["response"]["severity"] == "warning"


@pytest.mark.asyncio
async def test_api_mavlink_telemetry_flight(client):
    health = await client.get(f"{PREFIX}/health")
    assert health.status == 200
    body = await health.json()
    assert body["application_version"] == "1.7.0-alpha"
    assert body["mavlink_intelligence_ready"] is True

    msgs = await client.get(f"{PREFIX}/mavlink/messages")
    assert msgs.status == 200
    assert len((await msgs.json())["messages"]) > 5

    parse = await client.post(f"{PREFIX}/mavlink/parse", json={"payload": "VFR_HUD airspeed=12 groundspeed=10 alt=40"})
    assert parse.status == 200
    assert (await parse.json())["msg_name"] == "VFR_HUD"

    session_resp = await client.post(f"{PREFIX}/telemetry/sessions", json={"uav_id": "u1"})
    session = await session_resp.json()
    await client.post(
        f"{PREFIX}/telemetry/sessions/{session['session_id']}/samples",
        json={"battery": 90, "gps_fix": 12, "lat": 50.45, "lon": 30.52, "alt": 30, "rssi": 75},
    )
    analysis = await client.post(f"{PREFIX}/telemetry/analyze", json={"session_id": session["session_id"]})
    assert analysis.status == 200

    log = await client.post(
        f"{PREFIX}/flight-logs",
        json={"name": "a.tlog", "content": "HEARTBEAT type=1\nSTATUSTEXT text=OK\n", "filename": "a.tlog"},
    )
    assert log.status == 201

    diag = await client.post(f"{PREFIX}/diagnostics", json={"samples": [{"rc_loss": True}, {"ekf_error": True}]})
    assert diag.status == 201
    assert "rc_signal_loss" in (await diag.json())["detected_types"]

    mission_resp = await client.post(
        f"{PREFIX}/missions",
        json={"name": "M1", "waypoints": [{"lat": 50.45, "lon": 30.52, "alt": 40}, {"lat": 50.46, "lon": 30.53, "alt": 45}]},
    )
    mission = await mission_resp.json()
    intel = await client.post(f"{PREFIX}/mission-intel/analyze", json={"mission_id": mission["mission_id"], "battery_pct": 85})
    assert intel.status == 200

    gcs = await client.post(f"{PREFIX}/gcs/bridges", json={"name": "QGC", "gcs_type": "qgroundcontrol"})
    assert gcs.status == 201

    viz = await client.post(f"{PREFIX}/visualization/bundle", json={"session_id": session["session_id"]})
    assert viz.status == 200


def test_docs_and_knowledge_11_3():
    for name in ("MAVLINK.md", "TELEMETRY_AI.md", "FLIGHT_LOG_ANALYSIS.md", "DRONE_DIAGNOSTICS.md"):
        assert (ROOT / "docs" / name).exists()
    for name in (
        "TELEMETRY_REGISTRY.md",
        "FLIGHT_LOG_REGISTRY.md",
        "MAVLINK_REGISTRY.md",
        "DRONE_DASHBOARD.md",
        "MISSION_REGISTRY.md",
    ):
        assert (ROOT / "knowledge" / "drone" / name).exists()
    manifest = (ROOT / "applications" / "drone_platform" / "manifest.json").read_text()
    assert "1.7.0-alpha" in manifest
    assert "11.8" in manifest
