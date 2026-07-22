"""Tests — Resilient Navigation, Communications & Safety (Sprint 11.9)."""

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


def test_version_resilience_ready():
    health = drone_platform.health()
    assert health["application_version"] == "1.8.0-alpha"
    assert health["navigation_ready"] is True
    assert health["communications_ready"] is True
    assert health["safety_ready"] is True
    assert health["recovery_ready"] is True
    assert health["health_monitoring_ready"] is True
    assert health["drone_platform_production_ready"] is True
    assert health["engines"]["resilient_navigation"] == "1.0"
    assert health["engines"]["ai"] == "1.8"
    assert health["resilience_status"]["ready"] is True


def test_navigation_multi_source():
    nav = drone_platform.resilience.navigation
    session = nav.create_session(aircraft_id="ac1", sources=["gps", "imu"])
    sid = session["nav_session_id"]
    nav.update_gps(sid, fix_ok=True, sat_count=14, hdop=0.9, lat=50.45, lon=30.52, alt=40)
    nav.update_rtk(sid, fixed=True)
    nav.visual_navigation_interface(sid, enabled=True, quality=0.85)
    estimate = nav.multi_source_estimate(sid)
    assert estimate["confidence"] > 0.5
    assert "gps" in estimate["sources_used"] or "rtk" in estimate["sources_used"]
    conf = nav.position_confidence(sid)
    assert conf["level"] in {"high", "medium", "low"}
    health = nav.navigation_health(sid)
    assert health["health"] in {"healthy", "degraded", "critical"}
    # GPS denied → dead reckoning
    nav.update_gps(sid, fix_ok=False, sat_count=0, hdop=99)
    dr = nav.dead_reckoning(sid, dt_s=2.0, vx=5, vy=0)
    assert dr["active"] is True


def test_communications_failover():
    comm = drone_platform.resilience.communications
    link = comm.open_link(aircraft_id="ac1", primary="lte", secondary="radio")
    lid = link["link_id"]
    assert comm.link_quality(lid)["active"] == "lte"
    comm.update_quality(lid, channel="lte", quality=0.2, latency_ms=300, up=True)
    switched = comm.automatic_link_switching(lid, quality_threshold=0.5)
    assert switched["switched"] is True
    assert switched["active"] == "radio"
    assert comm.telemetry_router(lid)["telemetry_path"]
    assert comm.bandwidth_optimizer(lid)["profile"]["mode"] in {"full", "reduced", "critical"}
    assert "active_latency_ms" in comm.latency_monitor(lid)
    assert comm.recorder(lid, enable=True)["enabled"] is True
    assert "issues" in comm.diagnostics(lid)


def test_safety_and_health_and_recovery():
    safety = drone_platform.resilience.safety
    policy = safety.create_policy(aircraft_id="ac1", max_alt_m=100, min_battery_pct=30)
    sid = policy["safety_id"]
    safety.set_geofence(sid, south=50.44, north=50.46, west=30.51, east=30.53)
    ok = safety.check_position(sid, lat=50.45, lon=30.52, alt_m=40, speed_mps=8, battery_pct=70)
    assert ok["safe"] is True
    bad = safety.check_position(sid, lat=50.45, lon=30.52, alt_m=150, battery_pct=10, esc_temp_c=95)
    assert "altitude_exceeded" in bad["violations"]
    assert "battery_critical" in bad["violations"]
    assert safety.list_nofly_zones()
    assert safety.flight_envelope(sid)["envelope"]["max_alt_m"] == 100

    health = drone_platform.resilience.health
    snap = health.open(aircraft_id="ac1")
    hid = snap["health_id"]
    health.update(hid, section="battery", values={"pct": 15, "status": "warn"})
    overview = health.overview(hid)
    assert overview["overall"] in {"degraded", "critical", "healthy"}
    assert health.sensor_health(hid)["sensors"]
    assert health.cpu_ram_monitor(hid)["cpu_ram"]

    recovery = drone_platform.resilience.recovery
    evt = recovery.start(aircraft_id="ac1", reason="lost_link", mode="rtl", home={"lat": 50.45, "lon": 30.52})
    rid = evt["recovery_id"]
    recovery.automatic_return(rid)
    recovery.connection_recovery(rid, link="radio")
    recovery.sensor_reconfiguration(rid, disabled=["gps"], enabled=["imu", "visual"])
    recovery.safe_landing(rid)
    recovery.complete(rid, outcome="safe")
    report = recovery.report(rid)
    assert report["steps"] >= 4
    assert drone_platform.resilience.visualization.recovery_timeline(report=report)["type"] == "recovery_timeline"


def test_safety_ai():
    caps = drone_platform.ai.capabilities()
    assert "estimate_navigation_confidence" in caps
    assert "recommend_safe_actions" in caps
    conf = drone_platform.ai.assist(agent="estimate_navigation_confidence", query="c", context={"sources": ["gps", "rtk"], "gps_ok": True})
    assert conf["response"]["confidence"] > 0
    risk = drone_platform.ai.assist(agent="estimate_mission_risk", query="r", context={"nav_confidence": 0.3, "link_quality": 0.2, "battery_pct": 20})
    assert risk["response"]["risk_level"] in {"medium", "high"}
    actions = drone_platform.ai.assist(agent="recommend_safe_actions", query="battery low", context={"violations": ["battery_critical"]})
    assert actions["response"]["actions"]
    explain = drone_platform.ai.assist(agent="explain_recommendations", query="rtl_or_land_nearest")
    assert "explanation" in explain["response"]


@pytest.mark.asyncio
async def test_api_resilience(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "1.8.0-alpha"
    assert body["drone_platform_production_ready"] is True

    status = await client.get(f"{PREFIX}/resilience")
    assert status.status == 200
    assert (await status.json())["ready"] is True

    nav = await client.post(f"{PREFIX}/resilience/navigation", json={"aircraft_id": "ac1"})
    assert nav.status == 201
    sid = (await nav.json())["nav_session_id"]
    gps = await client.post(f"{PREFIX}/resilience/navigation", json={"action": "gps", "nav_session_id": sid, "fix_ok": True, "lat": 50.45, "lon": 30.52})
    assert gps.status == 200

    link = await client.post(f"{PREFIX}/resilience/communications", json={"aircraft_id": "ac1"})
    assert link.status == 201

    policy = await client.post(f"{PREFIX}/resilience/safety", json={"aircraft_id": "ac1"})
    assert policy.status == 201

    hlth = await client.post(f"{PREFIX}/resilience/health", json={"aircraft_id": "ac1"})
    assert hlth.status == 201

    rcv = await client.post(f"{PREFIX}/resilience/recovery", json={"aircraft_id": "ac1", "reason": "test"})
    assert rcv.status == 201


def test_docs_and_knowledge_11_9():
    for name in ("NAVIGATION.md", "COMMUNICATIONS.md", "SAFETY.md", "RECOVERY.md", "HEALTH_MONITORING.md"):
        assert (ROOT / "docs" / name).exists()
    for name in (
        "NAVIGATION_REGISTRY.md",
        "COMMUNICATION_REGISTRY.md",
        "SAFETY_REGISTRY.md",
        "RECOVERY_REGISTRY.md",
        "KNOWLEDGE_GRAPH.md",
        "DRONE_DASHBOARD.md",
    ):
        assert (ROOT / "knowledge" / "drone" / name).exists()
    manifest = (ROOT / "applications" / "drone_platform" / "manifest.json").read_text()
    assert "1.8.0-alpha" in manifest
    assert "11.9" in manifest
