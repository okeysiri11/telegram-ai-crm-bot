"""Tests — Visual Simulation Engine (Sprint 29.7)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.simulation.catalogs import SUPPORTED_SIMULATIONS, WIZARD_STEPS


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/platform-builder/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_platform_builder_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    platform_builder.reset()
    yield
    platform_builder.reset()


def test_simulation_engine_ready():
    health = platform_builder.health()
    assert health["application_version"] == "1.66.0"
    assert health["sprint"] == "34.0"
    assert health["simulation_engine_ready"] is True
    assert health["timeline_ready"] is True
    assert health["live_simulation_ready"] is True
    assert health["simulation_performance_optimized"] is True
    assert health["visual_event_bus_connected"] is True
    assert health["engines"]["simulation_engine"] == "1.0"
    assert health["engines"]["timeline_engine"] == "1.0"
    assert health["engines"]["simulation_api"] == "1.0"
    assert health["simulation"]["creates_fake_events"] is False
    assert health["simulation"]["originates_from_visual_event_bus"] is True

    catalog = platform_builder.simulation.catalog()
    assert catalog["operational"] is True
    assert catalog["creates_fake_events"] is False
    assert catalog["originates_from_visual_event_bus"] is True
    assert len(catalog["steps"]) == 10
    assert len(WIZARD_STEPS) == 10
    assert len(catalog["supported_simulations"]) == len(SUPPORTED_SIMULATIONS) == 22


def test_emit_ingest_timeline_create():
    eng = platform_builder.simulation
    overview = eng.engine_overview()
    assert "Simulation Registry" in overview["components"]
    assert overview["creates_fake_events"] is False

    emitted = eng.emit_and_simulate("Workflow Launch", {"workflow_id": "wf_1"})
    assert emitted["ok"] is True
    assert emitted["creates_fake_events"] is False
    assert emitted["frame"]["origin"] == "Visual Event Bus"
    assert emitted["event"]["event_type"] == "workflow_launch"

    ingested = eng.ingest_from_bus()
    assert ingested["creates_fake_events"] is False
    assert ingested["frame_count"] >= 1

    paused = eng.timeline_control("Pause")
    assert paused["paused"] is True
    resumed = eng.timeline_control("Resume")
    assert resumed["paused"] is False
    sped = eng.timeline_control("Speed Control", speed=2.0)
    assert sped["speed"] == 2.0
    stepped = eng.timeline_control("Step Forward")
    assert stepped["action"] == "Step Forward"

    perf = eng.performance()
    assert perf["frame_optimization"] is True
    assert perf["viewport_simulation"] is True

    session = eng.start_session()
    eng.update_session(session["session_id"], {"step": 10})
    created = eng.create(session["session_id"])
    assert created["ok"] is True
    assert created["simulation_engine"]["simulation_engine_id"]
    assert created["simulation_registry"]["simulation_registry_id"]
    assert created["timeline_engine"]["timeline_engine_id"]
    assert created["simulation_api"]["simulation_api_id"]
    assert created["simulation_engine"]["creates_fake_events"] is False


@pytest.mark.asyncio
async def test_api_simulation(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "1.66.0"
    assert body["simulation_engine_ready"] is True

    catalog = await client.get(f"{PREFIX}/simulation/catalog")
    assert catalog.status == 200
    assert (await catalog.json())["creates_fake_events"] is False

    emit = await client.post(
        f"{PREFIX}/simulation/emit",
        json={"simulation": "Task Completion"},
    )
    assert emit.status == 201
    assert (await emit.json())["originates_from_visual_event_bus"] is True

    session = await client.post(f"{PREFIX}/simulation/sessions", json={})
    assert session.status == 201
    sid = (await session.json())["session_id"]

    create = await client.post(f"{PREFIX}/simulation/sessions/{sid}/create", json={})
    assert create.status == 201
    assert (await create.json())["ok"] is True

    studio = ROOT / "src" / "web" / "platform-builder" / "simulation" / "SimulationEngineStudio.tsx"
    page = ROOT / "src" / "web" / "platform-builder" / "pages" / "SimulationEnginePage.tsx"
    assert studio.exists()
    assert page.exists()

    docs = ROOT / "docs" / "VISUAL_SIMULATION_ENGINE.md"
    assert docs.exists()
    knowledge = ROOT / "knowledge" / "simulation" / "README.md"
    assert knowledge.exists()

    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.66.0"' in manifest
    assert "33.6" in manifest
