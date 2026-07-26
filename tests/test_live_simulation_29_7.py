"""Tests — Live Enterprise Simulation (Sprint 29.7)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.simulation.catalogs import (
    COLLABORATION_VISUALS,
    DOCUMENT_FLOW,
    KNOWLEDGE_FLOW,
    LIVE_ORG_SURFACES,
    WORKFLOW_STAGES,
)


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


def test_live_enterprise_surfaces():
    health = platform_builder.health()
    assert health["live_simulation_ready"] is True
    assert health["application_version"] == "1.50.0"

    eng = platform_builder.simulation
    # Seed real bus events for each domain
    for name in (
        "Department Creation",
        "AI Activation",
        "Workflow Launch",
        "Knowledge Update",
        "Document Review",
    ):
        result = eng.emit_and_simulate(name)
        assert result["creates_fake_events"] is False

    live = eng.live_organization_simulation()
    assert set(live["surfaces"]) == set(LIVE_ORG_SURFACES)
    assert live["originates_from_visual_event_bus"] is True
    assert live["event_count"] >= 1

    collab = eng.ai_collaboration()
    assert set(collab["visuals"]) == set(COLLABORATION_VISUALS)
    assert collab["event_count"] >= 1

    workflow = eng.workflow_simulation()
    assert list(workflow["stages"]) == list(WORKFLOW_STAGES)

    knowledge = eng.knowledge_flow()
    assert list(knowledge["stages"]) == list(KNOWLEDGE_FLOW)

    document = eng.document_flow()
    assert list(document["stages"]) == list(DOCUMENT_FLOW)
    assert document["event_count"] >= 1

    ui = eng.ui_dashboard()
    assert ui["active_simulation_counter"] >= 1
    assert "Live Timeline" in ui["surfaces"]
    assert ui["creates_fake_events"] is False


@pytest.mark.asyncio
async def test_api_live_simulation(client):
    await client.post(f"{PREFIX}/simulation/emit", json={"simulation": "Organization Creation"})

    live = await client.get(f"{PREFIX}/simulation/live-organization")
    assert live.status == 200
    assert (await live.json())["creates_fake_events"] is False

    ui = await client.get(f"{PREFIX}/simulation/ui")
    assert ui.status == 200
    body = await ui.json()
    assert "organization_activity_feed" in body

    docs = ROOT / "docs" / "LIVE_ENTERPRISE_SIMULATION.md"
    assert docs.exists()
    knowledge = ROOT / "knowledge" / "live_visualization" / "README.md"
    assert knowledge.exists()
