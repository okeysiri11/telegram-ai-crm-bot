"""Tests — Drone Firmware Intelligence (Sprint 11.2)."""

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


def test_version_firmware_intelligence_ready():
    health = drone_platform.health()
    assert health["application_version"] == "1.8.0-alpha"
    assert health["firmware_intelligence_ready"] is True
    assert health["ardupilot_ready"] is True
    assert health["mission_planner_ready"] is True
    assert health["firmware_ai_assistant_ready"] is True
    assert health["engines"]["firmware"] == "1.1"


def test_firmware_repository_analyze_compare_build_sign_release():
    fw = drone_platform.firmware.create_project(name="Copter FW", stack="ardupilot", version="4.5.0")
    left = drone_platform.firmware_intel.repository.add_artifact(
        name="baseline.param",
        artifact_type=".param",
        content="ATC_RAT_PIT_P,0.10\nBATT_CAPACITY,5000\n",
        firmware_project_id=fw.firmware_project_id,
        version="4.5.0",
    )
    right = drone_platform.firmware_intel.repository.add_artifact(
        name="tuned.param",
        artifact_type=".param",
        content="ATC_RAT_PIT_P,0.12\nBATT_CAPACITY,5000\nFENCE_ENABLE,1\n",
        firmware_project_id=fw.firmware_project_id,
        version="4.5.0-tuned",
    )
    analysis = drone_platform.firmware_intel.analyzer.analyze_artifact(left["artifact_id"])
    assert analysis["parameter_count"] == 2
    diff = drone_platform.firmware_intel.comparator.compare_artifacts(left["artifact_id"], right["artifact_id"])
    assert any(c["parameter"] == "ATC_RAT_PIT_P" for c in diff["changed"])
    build = drone_platform.firmware_intel.builder.release_build(fw.firmware_project_id)
    assert build["status"] == "succeeded"
    sig = drone_platform.firmware_intel.signing.sign_artifact(left["artifact_id"])
    assert drone_platform.firmware_intel.signing.verify(sig["signature_id"])["valid"] is True
    release = drone_platform.firmware_intel.releases.create_release(
        firmware_project_id=fw.firmware_project_id,
        version="4.5.1",
        notes="Tuning + fence",
        artifact_ids=[right["artifact_id"]],
    )
    assert release["version"] == "4.5.1"
    patch = drone_platform.firmware_intel.patches.create_patch(
        firmware_project_id=fw.firmware_project_id,
        title="Raise pitch P",
        diff="+ ATC_RAT_PIT_P 0.12",
    )
    assert patch["status"] == "proposed"


def test_ardupilot_vehicles_params_modes_branches():
    project = drone_platform.ardupilot.create_project(name="Dev Copter", vehicle_type="copter", branch="Copter-4.5")
    assert project["vehicle_type"] == "copter"
    assert "ATC_RAT_PIT_P" in project["parameters"]
    params = drone_platform.ardupilot.parameter_database("copter")
    assert any(p["name"] == "FRAME_TYPE" for p in params)
    modes = drone_platform.ardupilot.modes("copter")
    assert any(m["name"] == "LOITER" for m in modes)
    for vehicle in ("plane", "rover", "boat", "sub", "custom"):
        profile = drone_platform.ardupilot.create_vehicle_profile(name=f"{vehicle}-profile", vehicle_type=vehicle)
        assert profile["vehicle_type"] == vehicle
    branch = drone_platform.ardupilot.create_branch(name="feature/tune", base="Copter-4.5")
    assert branch["name"] == "feature/tune"
    drone_platform.ardupilot.add_mission_template(
        name="Survey",
        vehicle_type="copter",
        waypoints=[{"sequence": 1, "latitude": 0, "longitude": 0, "altitude_m": 40}],
    )
    assert len(drone_platform.ardupilot.list_mission_library()) == 1


def test_mission_planner_import_export_waypoints():
    imported = drone_platform.mission_planner.import_mission(
        {
            "name": "MP Mission",
            "waypoints": [{"sequence": 1, "latitude": 1.0, "longitude": 36.0, "altitude_m": 50}],
            "geofences": [{"name": "pad", "vertices": [{"lat": 1.0, "lon": 36.0}]}],
        }
    )
    mission_id = imported["mission"]["mission_id"]
    exported = drone_platform.mission_planner.export_mission(mission_id)
    assert "MP Mission" in exported
    edited = drone_platform.mission_planner.edit_waypoints(
        mission_id,
        [
            {"sequence": 1, "latitude": 1.0, "longitude": 36.0, "altitude_m": 50},
            {"sequence": 2, "latitude": 1.1, "longitude": 36.1, "altitude_m": 55},
        ],
    )
    assert len(edited["waypoints"]) == 2
    drone_platform.mission_planner.save_flight_mode_profile(name="copter-basic", modes=["STABILIZE", "LOITER", "RTL"])
    assert drone_platform.mission_planner.list_profiles()


def test_firmware_ai_assistant():
    caps = drone_platform.ai.capabilities()
    assert "explain_firmware" in caps
    assert "generate_patches" in caps
    session = drone_platform.ai.assist(
        agent="suggest_parameter_tuning",
        query="oscillation in pitch",
        context={"vehicle": "copter"},
    )
    assert session["agent"] == "suggest_parameter_tuning"
    preset = drone_platform.ai.assist(
        agent="generate_configuration_presets",
        query="copter",
        context={"vehicle": "copter", "use_case": "default"},
    )
    assert preset["response"]["preset"]["parameters"]


def test_docs_present():
    for name in ("DRONE_FIRMWARE.md", "ARDUPILOT.md", "MISSION_PLANNER.md", "FIRMWARE_WORKFLOW.md"):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "drone" / "FIRMWARE_DASHBOARD.md").exists()


@pytest.mark.asyncio
async def test_api_firmware_intelligence(client: TestClient):
    health = await client.get(f"{PREFIX}/health")
    assert health.status == 200
    body = await health.json()
    assert body["application_version"] == "1.8.0-alpha"
    assert body["firmware_intelligence_ready"] is True

    status = await client.get(f"{PREFIX}/firmware/intelligence")
    assert status.status == 200

    fw = await client.post(
        f"{PREFIX}/firmware/projects",
        json={"name": "API FW", "stack": "px4", "version": "1.14"},
    )
    assert fw.status == 201
    fw_id = (await fw.json())["firmware_project_id"]

    art = await client.post(
        f"{PREFIX}/firmware/artifacts",
        json={
            "name": "a.param",
            "artifact_type": ".param",
            "content": "FOO,1\nBAR,2\n",
            "firmware_project_id": fw_id,
        },
    )
    assert art.status == 201
    art_id = (await art.json())["artifact_id"]

    analyzed = await client.post(f"{PREFIX}/firmware/analyze", json={"artifact_id": art_id})
    assert analyzed.status == 200
    assert (await analyzed.json())["parameter_count"] == 2

    built = await client.post(
        f"{PREFIX}/firmware/build",
        json={"firmware_project_id": fw_id, "profile": "debug"},
    )
    assert built.status == 201

    ap = await client.post(
        f"{PREFIX}/ardupilot/projects",
        json={"name": "API Ardu", "vehicle_type": "plane"},
    )
    assert ap.status == 201

    modes = await client.get(f"{PREFIX}/ardupilot/modes?vehicle=plane")
    assert modes.status == 200
    assert (await modes.json())["modes"]

    mp = await client.post(
        f"{PREFIX}/mission-planner/import",
        json={"name": "API MP", "waypoints": [{"latitude": 0, "longitude": 0, "altitude_m": 30}]},
    )
    assert mp.status == 201

    ai = await client.post(
        f"{PREFIX}/ai/assist",
        json={"agent": "explain_firmware", "query": "ardupilot", "context": {"stack": "ardupilot", "version": "4.5"}},
    )
    assert ai.status == 200
    assert (await ai.json())["agent"] == "explain_firmware"
