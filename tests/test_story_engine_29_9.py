"""Tests — Visual Story Engine (Sprint 29.9)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.story.catalogs import STORY_TYPES, WIZARD_STEPS


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


def test_story_engine_ready():
    health = platform_builder.health()
    assert health["application_version"] == "1.62.0"
    assert health["sprint"] == "33.6"
    assert health["story_engine_ready"] is True
    assert health["story_timeline_ready"] is True
    assert health["executive_story_ready"] is True
    assert health["milestone_viewer_ready"] is True
    assert health["engines"]["story_engine"] == "1.0"
    assert health["engines"]["story_timeline"] == "1.0"
    assert health["engines"]["executive_story_api"] == "1.0"
    assert health["story"]["creates_business_events"] is False
    assert health["story"]["reorders_business_events"] is False
    assert health["story"]["groups_verified_bus_events_only"] is True

    catalog = platform_builder.story.catalog()
    assert catalog["operational"] is True
    assert catalog["modifies_business_events"] is False
    assert len(catalog["steps"]) == 10
    assert len(WIZARD_STEPS) == 10
    assert set(catalog["story_types"]) == set(STORY_TYPES)


def test_build_from_bus_and_create():
    # Seed verified bus events (platform visual activity via simulation emit)
    platform_builder.simulation.emit_and_simulate("AI Activation")
    platform_builder.simulation.emit_and_simulate("Organization Creation")
    platform_builder.simulation.emit_and_simulate("Workflow Completion")

    eng = platform_builder.story
    overview = eng.engine_overview()
    assert overview["creates_business_events"] is False
    assert overview["reorders_business_events"] is False

    story = eng.build_story("AI Agent Story")
    assert story["frame_count"] >= 1
    assert story["creates_business_events"] is False
    assert story["modifies_business_events"] is False
    assert story["reorders_business_events"] is False
    assert all(f["verified_bus_event"] for f in story["frames"])
    # Chronological order preserved
    stamps = [f["published_at"] for f in story["frames"]]
    assert stamps == sorted(stamps)

    executive = eng.executive_mode()
    assert "Today's Progress" in executive["summaries"]
    assert executive["milestone_viewer"]["ready"] is True

    session = eng.start_session()
    eng.update_session(session["session_id"], {"step": 10, "draft": {"story_type": "Executive Story"}})
    created = eng.create(session["session_id"])
    assert created["ok"] is True
    assert created["story_engine"]["story_engine_id"]
    assert created["story_registry"]["story_registry_id"]
    assert created["story_builder"]["story_builder_id"]
    assert created["story_timeline"]["story_timeline_id"]
    assert created["executive_story_api"]["executive_story_api_id"]
    assert created["story_engine"]["reorders_business_events"] is False


@pytest.mark.asyncio
async def test_api_story(client):
    await client.post(f"{PREFIX}/simulation/emit", json={"simulation": "Knowledge Update"})

    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "1.62.0"
    assert body["story_engine_ready"] is True

    catalog = await client.get(f"{PREFIX}/story/catalog")
    assert catalog.status == 200
    assert (await catalog.json())["creates_business_events"] is False

    build = await client.post(
        f"{PREFIX}/story/build",
        json={"story_type": "Knowledge Story"},
    )
    assert build.status == 201
    assert (await build.json())["reorders_business_events"] is False

    session = await client.post(f"{PREFIX}/story/sessions", json={})
    assert session.status == 201
    sid = (await session.json())["session_id"]

    create = await client.post(f"{PREFIX}/story/sessions/{sid}/create", json={})
    assert create.status == 201
    assert (await create.json())["ok"] is True

    studio = ROOT / "src" / "web" / "platform-builder" / "story" / "StoryEngineStudio.tsx"
    page = ROOT / "src" / "web" / "platform-builder" / "pages" / "StoryEnginePage.tsx"
    assert studio.exists()
    assert page.exists()

    docs = ROOT / "docs" / "VISUAL_STORY_ENGINE.md"
    assert docs.exists()
    knowledge = ROOT / "knowledge" / "story_engine" / "README.md"
    assert knowledge.exists()

    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.62.0"' in manifest
    assert "33.6" in manifest
