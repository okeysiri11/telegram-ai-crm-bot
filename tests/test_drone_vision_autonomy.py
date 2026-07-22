"""Tests — Computer Vision / Navigation / Autonomy (Sprint 11.4)."""

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


def test_version_vision_autonomy_ready():
    health = drone_platform.health()
    assert health["application_version"] == "1.7.0-alpha"
    assert health["computer_vision_ready"] is True
    assert health["navigation_ai_ready"] is True
    assert health["autonomous_flight_ready"] is True
    assert health["slam_ready"] is True
    assert health["simulation_ready"] is True
    assert health["drone_ai_vision_platform_ready"] is True
    assert health["vision_flight_ai_ready"] is True
    assert health["engines"]["vision"] == "1.0"
    assert health["engines"]["ai"] == "1.7"


def test_vision_cameras_pipeline_detection_tracking():
    cams = drone_platform.vision.register_multi_camera(
        uav_id="uav_1",
        cameras=[
            {"name": "front", "camera_type": "rgb"},
            {"name": "stereo", "camera_type": "stereo"},
            {"name": "thermal", "camera_type": "thermal"},
            {"name": "night", "camera_type": "night_vision"},
            {"name": "depth", "camera_type": "depth"},
        ],
    )
    assert len(cams) == 5
    assert drone_platform.vision.support_matrix()["stereo_camera"] is True
    stream = drone_platform.vision.streams.open(camera_id=cams[0]["camera_id"])
    frame = drone_platform.vision.frames.process(stream_id=stream["stream_id"])
    pipe = drone_platform.vision.pipeline.run(frame)
    assert pipe["output"] == "pipeline_complete"
    det = drone_platform.detection.detector.detect(frame_id=frame["frame_id"])
    assert det["count"] >= 1
    for method in (
        "vehicle_detection",
        "person_detection",
        "aircraft_detection",
        "ship_detection",
        "building_detection",
        "road_detection",
        "tree_detection",
        "power_line_detection",
        "landing_zone_detection",
        "obstacle_detection",
    ):
        getattr(drone_platform.detection, method)(frame["frame_id"])
    track = drone_platform.detection.tracker.start_track(detection_id=det["detections"][0]["detection_id"])
    updated = drone_platform.detection.tracker.update(track["track_id"], bbox=[1, 2, 3, 4])
    assert len(updated["history"]) == 2
    classified = drone_platform.detection.detector.classify(det["detections"][0]["detection_id"])
    assert "classified_as" in classified


def test_navigation_modes():
    nav = drone_platform.navigation
    assert nav.visual_navigation(landmarks=[{"id": "l1"}], current={"lat": 50.45, "lon": 30.52})["mode"] == "visual"
    assert nav.gps_assisted(waypoints=[{"lat": 50.45, "lon": 30.52}])["mode"] == "gps_assisted"
    assert nav.gps_denied(visual_fix=True)["status"] == "ready"
    assert nav.terrain_following(clearance_m=25)["clearance_m"] == 25
    avoid = nav.obstacle_avoidance(obstacles=[{"distance_m": 10, "bearing_deg": 20}])
    assert avoid["avoid"] is True
    path = nav.dynamic_path_planning(
        start={"lat": 50.45, "lon": 30.52, "alt": 40},
        goal={"lat": 50.46, "lon": 30.53, "alt": 50},
        obstacles=[{"id": "tree"}],
    )
    assert len(path["path"]) == 3
    lz = nav.safe_landing_finder(candidates=[{"lat": 50.45, "lon": 30.52, "flatness": 0.9, "clearance": 0.8, "confidence": 0.7}])
    assert lz["primary"]["score"] > 0
    route = nav.route_optimizer(
        waypoints=[
            {"lat": 50.45, "lon": 30.52},
            {"lat": 50.45001, "lon": 30.52001},
            {"lat": 50.46, "lon": 30.53},
        ]
    )
    assert route["waypoint_count"] >= 2
    emergency = nav.emergency_route(
        current={"lat": 50.45, "lon": 30.52},
        home={"lat": 50.451, "lon": 30.521},
        battery_pct=40,
    )
    assert emergency["action"] in {"rth", "land_immediate"}


def test_mapping_slam_and_mission_map():
    slam = drone_platform.mapping.visual_slam(frame_ids=["frm_1", "frm_2"], seed_pose={"x": 0, "y": 0, "z": 1})
    drone_platform.mapping.feature_mapping(map_id=slam["map_id"], features=[{"id": "f1", "x": 1, "y": 2}])
    cloud = drone_platform.mapping.point_cloud(map_id=slam["map_id"])
    recon = drone_platform.mapping.reconstruct_3d(map_id=slam["map_id"], point_cloud_id=cloud["point_cloud_id"])
    assert recon["reconstruction"]["mesh_ready"] is True
    terrain = drone_platform.mapping.terrain_mapping(bounds={"north": 50.5, "south": 50.4, "east": 30.6, "west": 30.5})
    drone_platform.mapping.orthophoto(map_id=terrain["map_id"])
    drone_platform.mapping.digital_elevation_model(map_id=terrain["map_id"])
    cache = drone_platform.mapping.local_map_cache(map_id=terrain["map_id"])
    assert cache["cached"] is True
    mmap = drone_platform.mapping.mission_map_builder(
        mission_id="msn_1",
        waypoints=[{"lat": 50.45, "lon": 30.52}, {"lat": 50.46, "lon": 30.53}],
    )
    assert mmap["map_type"] == "mission"


def test_autonomous_flight_modes():
    auto = drone_platform.autonomy
    assert auto.takeoff_assistant(target_alt_m=12)["go"] is True
    assert auto.landing_assistant(zone={"lat": 50.45, "lon": 30.52})["mode"] == "landing"
    patrol = auto.autonomous_patrol(waypoints=[{"lat": 50.45, "lon": 30.52}, {"lat": 50.46, "lon": 30.53}])
    assert patrol["mode"] == "patrol"
    assert auto.waypoint_ai(waypoints=[{"lat": 50.45, "lon": 30.52}])["adapt"] is True
    assert auto.target_following(track_id="trk_1")["standoff_m"] == 15
    assert auto.orbit_mode(center={"lat": 50.45, "lon": 30.52})["radius_m"] == 50
    search = auto.search_pattern(bounds={"south": 50.45, "north": 50.451, "west": 30.52, "east": 30.521}, spacing_m=50)
    assert search["count"] >= 2
    coverage = auto.area_coverage(bounds={"south": 50.45, "north": 50.451, "west": 30.52, "east": 30.521})
    assert coverage["mode"] == "area_coverage"
    swarm = auto.swarm_ready(vehicle_ids=["v1", "v2", "v3"])
    assert swarm["architecture_ready"] is True
    decision = auto.decision_engine(observations={"obstacle_near": True}, battery_pct=20, link_ok=False)
    assert decision["primary"]["action"] in {"rth_or_land", "failsafe_hold", "avoid"}


def test_simulation_sitl_scenarios_replays():
    run = drone_platform.simulation.create_run(name="SITL demo", mission_id="msn_1")
    assert run["sitl_ready"] is True
    drone_platform.simulation.mark_sitl_ready(run["simulation_id"])
    timeline = drone_platform.simulation.simulation_timeline(simulation_id=run["simulation_id"])
    assert timeline["events"]
    scenario = drone_platform.simulation.build_scenario(name="windy", environment={"wind_mps": 8})
    sensors = drone_platform.simulation.virtual_sensors(scenario_id=scenario["scenario_id"])
    assert "gps" in sensors["sensors"]
    mreplay = drone_platform.simulation.mission_replay(mission_id="msn_1", waypoints=[{"lat": 1, "lon": 2}])
    assert mreplay["replay_type"] == "mission"
    vreplay = drone_platform.simulation.visual_replay(frame_ids=["frm_1"])
    assert vreplay["replay_type"] == "visual"
    assert drone_platform.simulation.status()["sitl_ready"] is True


def test_vision_flight_ai():
    caps = drone_platform.ai.capabilities()
    assert "recommend_flight_path" in caps
    assert "optimize_flight_altitude" in caps
    path = drone_platform.ai.assist(
        agent="recommend_flight_path",
        query="path",
        context={"start": {"lat": 1}, "goal": {"lat": 2}},
    )
    assert path["agent"] == "recommend_flight_path"
    unsafe = drone_platform.ai.detect_unsafe_conditions(observations={"battery_pct": 10, "wind_mps": 15})
    assert unsafe["response"]["unsafe"] is True


@pytest.mark.asyncio
async def test_api_vision_navigation_autonomy(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "1.7.0-alpha"
    assert body["computer_vision_ready"] is True

    cam = await client.post(f"{PREFIX}/vision/cameras", json={"name": "cam1", "camera_type": "rgb"})
    assert cam.status == 201
    camera = await cam.json()
    stream = await (await client.post(f"{PREFIX}/vision/streams", json={"camera_id": camera["camera_id"]})).json()
    frame_resp = await client.post(f"{PREFIX}/vision/frames", json={"stream_id": stream["stream_id"]})
    assert frame_resp.status == 201
    frame_body = await frame_resp.json()
    det = await client.post(f"{PREFIX}/vision/detect", json={"frame_id": frame_body["frame"]["frame_id"]})
    assert det.status == 201

    nav = await client.post(
        f"{PREFIX}/navigation/plan",
        json={
            "mode": "dynamic_path",
            "start": {"lat": 50.45, "lon": 30.52, "alt": 40},
            "goal": {"lat": 50.46, "lon": 30.53, "alt": 45},
        },
    )
    assert nav.status == 201

    slam = await client.post(f"{PREFIX}/mapping/slam", json={"frame_ids": [frame_body["frame"]["frame_id"]]})
    assert slam.status == 201

    auto = await client.post(f"{PREFIX}/autonomy/action", json={"mode": "takeoff", "target_alt_m": 10})
    assert auto.status == 201

    sim = await client.post(f"{PREFIX}/simulation/runs", json={"name": "run1"})
    assert sim.status == 201
    scn = await client.post(f"{PREFIX}/simulation/scenarios", json={"name": "s1"})
    assert scn.status == 201


def test_docs_and_knowledge_11_4():
    for name in ("COMPUTER_VISION.md", "NAVIGATION_AI.md", "AUTONOMOUS_FLIGHT.md", "SLAM_MAPPING.md"):
        assert (ROOT / "docs" / name).exists()
    for name in ("VISION_REGISTRY.md", "NAVIGATION_REGISTRY.md", "MAPPING_REGISTRY.md", "AUTONOMY_REGISTRY.md", "DRONE_DASHBOARD.md"):
        assert (ROOT / "knowledge" / "drone" / name).exists()
    manifest = (ROOT / "applications" / "drone_platform" / "manifest.json").read_text()
    assert "1.7.0-alpha" in manifest
    assert "11.8" in manifest
