"""Tests — Drone Engineering Suite (Sprint 11.5)."""

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


def test_version_engineering_suite_ready():
    health = drone_platform.health()
    assert health["application_version"] == "1.6.0-alpha"
    assert health["drone_engineering_ready"] is True
    assert health["battery_engineering_ready"] is True
    assert health["pcb_engineering_ready"] is True
    assert health["cad_integration_ready"] is True
    assert health["engineering_ai_ready"] is True
    assert health["drone_engineering_suite_ready"] is True
    assert health["engines"]["engineering_suite"] == "1.0"
    assert health["engines"]["ai"] == "1.6"


def test_airframe_designers_and_calculators():
    suite = drone_platform.engineering_suite
    assert len(suite.airframe.frame_database()) >= 3
    multi = suite.airframe.multirotor_designer(arms=4, wheelbase_mm=450, auw_kg=1.8)
    assert multi["frame_type"] == "multirotor"
    wing = suite.airframe.wing_calculator(span_m=1.8, chord_m=0.25)
    assert wing["wing_area_m2"] > 0
    fw = suite.airframe.flying_wing_designer(span_m=1.2, root_chord_m=0.3, tip_chord_m=0.15)
    assert fw["frame_type"] == "flying_wing"
    vtol = suite.airframe.vtol_designer(span_m=2.0, auw_kg=6)
    assert vtol["frame_type"] == "vtol"
    cg = suite.airframe.cg_calculator(stations=[{"mass_kg": 1.0, "x_mm": 0}, {"mass_kg": 0.5, "x_mm": 100}])
    assert cg["cg_mm"] == pytest.approx(33.33, rel=1e-2)
    payload = suite.airframe.payload_calculator(empty_kg=2.0, max_takeoff_kg=3.5)
    assert payload["max_payload_kg"] > 0
    structural = suite.airframe.structural_validator(auw_kg=2.0)
    assert "valid" in structural


def test_propulsion_and_motors():
    prop = drone_platform.engineering_suite.propulsion
    assert len(prop.motor_database()) >= 3
    assert len(prop.propeller_database()) >= 3
    assert len(prop.esc_database()) >= 2
    thrust = prop.thrust_calculator(diameter_in=10, pitch_in=4.7, rpm=8000)
    assert thrust["thrust_kgf"] > 0
    hover = prop.hover_calculator(auw_kg=1.5, motors=4, thrust_per_motor_kgf=1.0)
    assert hover["hover_ok"] is True
    eff = prop.efficiency_optimizer(candidates=[{"name": "a", "thrust_kgf": 1, "power_w": 100}, {"name": "b", "thrust_kgf": 1.2, "power_w": 90}])
    assert eff["best"]["name"] == "b"


def test_battery_engineering():
    batt = drone_platform.engineering_suite.battery
    pack = batt.support_18650(series=4, parallel=2)
    assert pack["configuration"] == "4S2P"
    pack2 = batt.support_21700(series=6, parallel=1)
    assert pack2["cell_type"] == "21700"
    lipo = batt.lipo_calculator(series=4, capacity_mah=5000, c_rating=30)
    assert lipo["max_continuous_a"] == 150.0
    ft = batt.flight_time_estimator(capacity_mah=5000, average_current_a=20)
    assert ft["flight_time_min"] > 0
    health = batt.battery_health(cycles=50, measured_capacity_mah=4500, rated_capacity_mah=5000)
    assert health["status"] in {"good", "degraded", "replace"}


def test_electronics_pcb_cad():
    elec = drone_platform.engineering_suite.electronics
    assert elec.elrs_support()["supported"] is True
    assert elec.crossfire_support()["supported"] is True
    assert len(elec.analog_fpv()) >= 1
    assert len(elec.digital_fpv()) >= 1
    bec = elec.bec_calculator(input_v=16.8, output_v=5.0, load_a=2.0)
    assert bec["input_current_a"] > 0
    pcb = drone_platform.engineering_suite.pcb
    project = pcb.create_project(name="PDB", components=[{"ref": "U1", "mpn": "STM32H743VIT6", "qty": 1}])
    bom = pcb.bom_generator(project["pcb_project_id"])
    assert bom["line_count"] == 1
    assert pcb.schematic_validator(project["pcb_project_id"])["valid"] is True
    assert pcb.gerber_export(project["pcb_project_id"])["files"]
    cad = drone_platform.engineering_suite.cad
    part = cad.register_part(name="arm", format="step")
    assert cad.step_support() is True
    asm = cad.create_assembly(name="frame", part_ids=[part["part_id"]])
    assert asm["part_count"] == 1
    assert cad.preview_3d(part["part_id"])["preview"]["status"] == "ready"
    assert cad.export(part["part_id"], target_format="stl")["target_format"] == "stl"


def test_engineering_simulation_and_ai():
    sim = drone_platform.engineering_suite.simulation
    perf = sim.flight_performance(auw_kg=1.5, thrust_kgf=4.0)
    assert perf["twr"] > 1
    assert sim.range_simulator(cruise_speed_mps=12, cruise_min=15)["range_km"] > 0
    assert sim.weather_impact(base_range_km=5, wind_mps=10, rain=True)["adjusted_range_km"] < 5
    caps = drone_platform.ai.capabilities()
    assert "recommend_motors" in caps
    assert "recommend_batteries" in caps
    motors = drone_platform.ai.assist(agent="recommend_motors", query="multirotor", context={"auw_kg": 2.0, "motors": 4})
    assert motors["agent"] == "recommend_motors"
    mistakes = drone_platform.ai.detect_engineering_mistakes(design={"twr": 1.1, "esc_amps": 20, "motor_amps": 30})
    assert mistakes["response"]["ok"] is False


@pytest.mark.asyncio
async def test_api_engineering_suite(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "1.6.0-alpha"
    assert body["drone_engineering_suite_ready"] is True

    status = await client.get(f"{PREFIX}/engineering/suite")
    assert status.status == 200
    assert (await status.json())["ready"] is True

    af = await client.post(f"{PREFIX}/engineering/airframes", json={"action": "multirotor", "arms": 4, "auw_kg": 1.5})
    assert af.status == 201

    prop = await client.get(f"{PREFIX}/engineering/propulsion")
    assert prop.status == 200
    assert len((await prop.json())["motors"]) >= 1

    batt = await client.post(
        f"{PREFIX}/engineering/batteries",
        json={"name": "Pack", "cell_type": "18650", "series": 4, "parallel": 2},
    )
    assert batt.status == 201

    pcb = await client.post(f"{PREFIX}/engineering/pcb", json={"name": "FC", "components": [{"ref": "U1", "mpn": "X"}]})
    assert pcb.status == 201

    cad = await client.post(f"{PREFIX}/engineering/cad", json={"name": "plate", "format": "stl"})
    assert cad.status == 201

    sim = await client.post(f"{PREFIX}/engineering/simulate", json={"kind": "flight_performance", "auw_kg": 1.5, "thrust_kgf": 3})
    assert sim.status == 201


def test_docs_and_knowledge_11_5():
    for name in ("ENGINEERING.md", "AIRFRAME.md", "POWER_SYSTEM.md", "BATTERY_ENGINEERING.md", "PCB_ENGINEERING.md", "CAD_INTEGRATION.md"):
        assert (ROOT / "docs" / name).exists()
    for name in (
        "ENGINEERING_REGISTRY.md",
        "COMPONENTS_REGISTRY.md",
        "BATTERY_REGISTRY.md",
        "CAD_REGISTRY.md",
        "PCB_REGISTRY.md",
        "KNOWLEDGE_GRAPH.md",
        "DRONE_DASHBOARD.md",
    ):
        assert (ROOT / "knowledge" / "drone" / name).exists()
    manifest = (ROOT / "applications" / "drone_platform" / "manifest.json").read_text()
    assert "1.6.0-alpha" in manifest
    assert "11.7" in manifest
