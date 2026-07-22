"""Tests — Port ERP AI Operations & Digital Twin (Sprint 9.6)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.port_erp import port_erp
from applications.port_erp.api.register import register_port_erp_routes
from applications.port_erp.digital_twin.models import AlertType, SimulationScenario, WeatherCondition
from applications.port_erp.shared.models import Berth, Port, Terminal, Vessel
from applications.port_erp.terminal_operations.models import Equipment, EquipmentType, YardBlock


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_port_erp_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    port_erp.reset()
    yield
    port_erp.reset()


def test_version_ai_ops_docs_bridges():
    health = port_erp.health()
    assert health["application_version"] == "2.0.0"
    assert health["ai_operations_engine"] == "1.0"
    assert "ai_ops" in health
    docs = Path(__file__).resolve().parents[1] / "docs" / "PORT_AI.md"
    assert docs.exists()
    assert "Digital Twin Engine" in docs.read_text(encoding="utf-8")
    assert port_erp.platform.platform_health()["platform_dependency"] == "AI Platform Core v3"
    assert port_erp.ecosystem.ecosystem_health()["ecosystem_dependency"] == "AI Ecosystem v1.5"
    root = Path(__file__).resolve().parents[1] / "applications" / "port_erp"
    for name in (
        "digital_twin",
        "executive_ai",
        "operations_center",
        "optimization",
        "berth_scheduler",
        "yard_optimizer",
        "resource_manager",
        "prediction",
        "simulation",
        "dashboard",
        "alerts",
    ):
        assert (root / name).is_dir()


@pytest.mark.asyncio
async def test_digital_twin_snapshot_and_weather():
    port = port_erp.core.ports.register(Port(name="AI Port", code="AIPT", country="KE"))
    terminal = port_erp.core.terminals.register(Terminal(name="CT1", port_id=port.port_id))
    port_erp.core.berths.register(
        Berth(name="B1", terminal_id=terminal.terminal_id, status="occupied")
    )
    port_erp.core.berths.register(
        Berth(name="B2", terminal_id=terminal.terminal_id, status="available")
    )
    port_erp.core.vessels.register(Vessel(name="Twin Ship"))
    port_erp.terminal.yard.create_block(
        YardBlock(terminal_id=terminal.terminal_id, name="YA", rows=1, slots_per_row=2)
    )
    await port_erp.terminal.yard.assign_slot("c1", terminal_id=terminal.terminal_id)

    weather = port_erp.ai_ops.twin.set_weather(
        condition=WeatherCondition.STORM, wind_knots=35, visibility_km=1.0
    )
    assert weather.condition == WeatherCondition.STORM

    snap = await port_erp.ai_ops.twin.snapshot(port_id=port.port_id)
    assert snap.ships >= 1
    assert snap.berths == 2
    assert snap.berths_occupied == 1
    assert snap.yards_slots == 2
    assert snap.yards_occupied == 1
    assert snap.weather.condition == WeatherCondition.STORM
    assert port_erp.ai_ops.twin.latest() is not None


@pytest.mark.asyncio
async def test_simulation_scenarios():
    assert len(port_erp.ai_ops.simulation.scenarios()) == 8
    run = await port_erp.ai_ops.simulation.run(SimulationScenario.PEAK_SEASON)
    assert run.scenario == SimulationScenario.PEAK_SEASON
    assert "volume_multiplier" in run.impact
    assert run.recommendations
    storm = await port_erp.ai_ops.simulation.run("storm_delays", name="Storm drill")
    assert storm.name == "Storm drill"
    assert len(port_erp.ai_ops.simulation.list_runs()) == 2


@pytest.mark.asyncio
async def test_optimization_and_executive_ai():
    port = port_erp.core.ports.register(Port(name="Opt Port", code="OPT1", country="KE"))
    terminal = port_erp.core.terminals.register(Terminal(name="T-Opt", port_id=port.port_id))
    port_erp.core.berths.register(
        Berth(name="B-AI", terminal_id=terminal.terminal_id, status="available")
    )
    port_erp.terminal.equipment.register(
        Equipment(
            name="STS-AI",
            equipment_type=EquipmentType.STS,
            terminal_id=terminal.terminal_id,
        )
    )
    plans = await port_erp.ai_ops.optimization.run_all(vessel_id="v1")
    assert len(plans) == 3
    assert {p.plan_type for p in plans} >= {"berth_allocation", "container_flow", "resource_balancing"}

    briefing = await port_erp.ai_ops.executive.briefing()
    assert "kpis" in briefing
    assert len(briefing["kpis"]) >= 8
    assert "recommendations" in briefing
    dash = port_erp.ai_ops.dashboard.dashboard()
    assert "bottlenecks" in dash


@pytest.mark.asyncio
async def test_operations_center_alerts():
    refreshed = await port_erp.ai_ops.operations.refresh(port_id="p1")
    assert "snapshot" in refreshed
    alert = await port_erp.ai_ops.alerts.raise_alert(
        alert_type=AlertType.EQUIPMENT_FAILURE,
        title="Crane offline",
        severity="critical",
    )
    assert alert.severity.value == "critical"
    ack = port_erp.ai_ops.alerts.acknowledge(alert.alert_id)
    assert ack.acknowledged is True
    overview = port_erp.ai_ops.operations.overview()
    assert "twin" in overview


@pytest.mark.asyncio
async def test_ai_ops_rest_api(client: TestClient):
    health = await client.get("/api/port/v1/health")
    assert health.status == 200
    body = await health.json()
    assert body["application_version"] == "2.0.0"
    assert body["ai_operations_engine"] == "1.0"

    twin = await client.get("/api/port/v1/digital-twin")
    assert twin.status == 200

    snap = await client.post("/api/port/v1/digital-twin/snapshot", json={})
    assert snap.status == 201

    weather = await client.post(
        "/api/port/v1/digital-twin/weather",
        json={"condition": "rain", "wind_knots": 12},
    )
    assert weather.status == 200

    dash = await client.get("/api/port/v1/dashboard")
    assert dash.status == 200

    center = await client.get("/api/port/v1/operations/center")
    assert center.status == 200

    scenarios = await client.get("/api/port/v1/simulation/scenarios")
    assert scenarios.status == 200
    assert len((await scenarios.json())["items"]) == 8

    sim = await client.post(
        "/api/port/v1/simulation/run",
        json={"scenario": "equipment_failures"},
    )
    assert sim.status == 201

    opt = await client.post("/api/port/v1/optimization/run", json={})
    assert opt.status == 200
    assert len((await opt.json())["items"]) == 3

    executive = await client.get("/api/port/v1/executive")
    assert executive.status == 200
    preds = await client.get("/api/port/v1/executive/predictions")
    assert preds.status == 200
