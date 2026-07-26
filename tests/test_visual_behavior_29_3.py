"""Tests — Visual Behavior Engine (Sprint 29.3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.visual_behavior.catalogs import BEHAVIORS, TRANSITIONS, WIZARD_STEPS


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


def test_visual_behavior_ready():
    health = platform_builder.health()
    assert health["application_version"] == "1.42.0"
    assert health["sprint"] == "32.2"
    assert health["visual_behavior_engine_ready"] is True
    assert health["animation_framework_ready"] is True
    assert health["transition_engine_ready"] is True
    assert health["behavior_performance_optimized"] is True
    assert health["engines"]["visual_behavior_engine"] == "1.0"
    assert health["engines"]["animation_framework"] == "1.0"
    assert health["engines"]["transition_engine"] == "1.0"
    assert health["visual_behavior"]["executes_business_logic"] is False

    catalog = platform_builder.visual_behavior.catalog()
    assert catalog["operational"] is True
    assert catalog["executes_business_logic"] is False
    assert catalog["reacts_to_visual_event_bus_only"] is True
    assert len(catalog["steps"]) == 10
    assert len(WIZARD_STEPS) == 10
    assert len(catalog["behaviors"]) == len(BEHAVIORS) == 11
    assert "Searching" in catalog["behaviors"]


def test_transitions_events_wait_create():
    vb = platform_builder.visual_behavior
    overview = vb.engine_overview()
    assert overview["executes_business_logic"] is False
    assert "visual_state" in overview["state_fields"]

    # Idle → Working is allowed
    result = vb.run_transition("ai_vb_1", "Working")
    assert result["transition"]["allowed"] is True
    assert result["object"]["behavior_state"]["current"] == "Working"

    # Working → Thinking
    result2 = vb.run_transition("ai_vb_1", "Thinking")
    assert result2["transition"]["allowed"] is True

    # Invalid jump blocked
    blocked = vb.transitions.transition("Idle", "Completed")
    assert blocked["allowed"] is False

    assert len(TRANSITIONS) == 5

    sub = vb.subscribe_events(["AI Events"])
    assert sub["active"] is True
    assert sub["applied"]["executes_business_logic"] is False

    wait = vb.wait_experience()
    assert wait["empty_loading"] is False
    assert wait["fake_processing"] is False
    assert wait["only_actual_execution_stages"] is True

    session = vb.start_session()
    vb.update_session(session["session_id"], {"step": 10})
    created = vb.create(session["session_id"])
    assert created["ok"] is True
    assert created["behavior_engine"]["behavior_engine_id"]
    assert created["animation_framework"]["animation_framework_id"]
    assert created["transition_engine"]["transition_engine_id"]
    assert created["behavior_engine"]["executes_business_logic"] is False


@pytest.mark.asyncio
async def test_api_visual_behavior(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "1.42.0"
    assert body["visual_behavior_engine_ready"] is True

    catalog = await client.get(f"{PREFIX}/visual-behavior/catalog")
    assert catalog.status == 200
    assert (await catalog.json())["executes_business_logic"] is False

    session = await client.post(f"{PREFIX}/visual-behavior/sessions", json={})
    assert session.status == 201
    sid = (await session.json())["session_id"]

    create = await client.post(f"{PREFIX}/visual-behavior/sessions/{sid}/create", json={})
    assert create.status == 201
    assert (await create.json())["ok"] is True


def test_docs_visual_behavior_29_3():
    assert (ROOT / "docs" / "VISUAL_BEHAVIOR_ENGINE.md").exists()
    assert (ROOT / "docs" / "ANIMATION_FRAMEWORK.md").exists()
    assert (ROOT / "knowledge" / "visual_behavior" / "README.md").exists()
    assert (ROOT / "knowledge" / "animation" / "README.md").exists()
    assert (
        ROOT / "src" / "web" / "platform-builder" / "visual-behavior" / "VisualBehaviorStudio.tsx"
    ).exists()
    docs = (ROOT / "docs" / "VISUAL_BEHAVIOR_ENGINE.md").read_text()
    for key in ("Business logic is NOT allowed", "Searching", "Transition"):
        assert key in docs
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.42.0"' in manifest
    assert "32.2" in manifest
