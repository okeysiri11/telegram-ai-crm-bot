"""Tests — Story Timeline (Sprint 29.9)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes


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


def test_story_timeline_navigation():
    health = platform_builder.health()
    assert health["story_timeline_ready"] is True
    assert health["milestone_viewer_ready"] is True
    assert health["application_version"] == "1.33.0"

    platform_builder.simulation.emit_and_simulate("Workflow Launch")
    platform_builder.simulation.emit_and_simulate("Task Assignment")
    platform_builder.simulation.emit_and_simulate("Workflow Completion")

    eng = platform_builder.story
    story = eng.build_story("Workflow Story")
    assert story["frame_count"] >= 1

    played = eng.navigate("Play")
    assert played["playing"] is True
    assert played["paused"] is False

    paused = eng.navigate("Pause")
    assert paused["paused"] is True

    stepped = eng.navigate("Step")
    assert stepped["action"] == "Step"

    if story["frame_count"] > 1:
        nav = eng.navigate("Timeline Navigation", index=0)
        assert nav["cursor"] == 0

    bm = eng.navigate("Bookmarks", label="Key beat")
    assert bm["bookmark"]["label"] == "Key beat"

    milestones = eng.milestone_viewer()
    assert milestones["ready"] is True

    ui = eng.ui_dashboard()
    assert "Story Timeline" in ui["surfaces"]
    assert "Milestone Viewer" in ui["surfaces"]
    assert ui["creates_business_events"] is False


@pytest.mark.asyncio
async def test_api_story_timeline(client):
    await client.post(f"{PREFIX}/simulation/emit", json={"simulation": "Document Approval"})
    await client.post(f"{PREFIX}/story/build", json={"story_type": "Document Story"})

    play = await client.post(f"{PREFIX}/story/navigate", json={"action": "Play"})
    assert play.status == 200
    assert (await play.json())["playing"] is True

    timeline = await client.get(f"{PREFIX}/story/timeline")
    assert timeline.status == 200

    milestones = await client.get(f"{PREFIX}/story/milestones")
    assert milestones.status == 200

    executive = await client.get(f"{PREFIX}/story/executive")
    assert executive.status == 200
    body = await executive.json()
    assert body["reorders_business_events"] is False

    docs = ROOT / "docs" / "ENTERPRISE_STORYTELLING.md"
    assert docs.exists()
    knowledge = ROOT / "knowledge" / "storytelling" / "README.md"
    assert knowledge.exists()
