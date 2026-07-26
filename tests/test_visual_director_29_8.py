"""Tests — Visual Director Engine (Sprint 29.8)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.director.catalogs import DIRECTOR_COMPONENTS, WIZARD_STEPS


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


def test_director_engine_ready():
    health = platform_builder.health()
    assert health["application_version"] == "1.54.0"
    assert health["sprint"] == "32.8"
    assert health["director_engine_ready"] is True
    assert health["scene_manager_ready"] is True
    assert health["focus_engine_ready"] is True
    assert health["priority_manager_ready"] is True
    assert health["engines"]["director_engine"] == "1.0"
    assert health["engines"]["scene_manager"] == "1.0"
    assert health["engines"]["focus_manager"] == "1.0"
    assert health["engines"]["priority_manager"] == "1.0"
    assert health["director"]["generates_business_events"] is False
    assert health["director"]["orchestrates_visual_presentation_only"] is True

    catalog = platform_builder.director.catalog()
    assert catalog["operational"] is True
    assert catalog["generates_business_events"] is False
    assert catalog["orchestrates_visual_presentation_only"] is True
    assert len(catalog["steps"]) == 10
    assert len(WIZARD_STEPS) == 10
    assert set(catalog["director_components"]) == set(DIRECTOR_COMPONENTS)


def test_focus_coord_create():
    eng = platform_builder.director
    overview = eng.director_overview()
    assert overview["generates_business_events"] is False
    assert "Focus Manager" in overview["components"]

    focus = eng.focus_engine({"ai_priority": 0.99})
    assert focus["primary_focus"]["target"] == "Highest Priority AI"

    attention = eng.attention_management()
    assert attention["current_highlight"]["ref"]
    assert len(attention["attention_queue"]) >= 1

    coord = eng.simulation_coordination()
    assert "Behavior Engine" in coord["engines"]
    assert coord["generates_business_events"] is False

    camera = eng.camera_api(zoom=1.2, focus_target="ai_specialist_1")
    assert camera["camera"]["zoom_target"] == 1.2
    assert camera["future_ai_city_navigation"]["ready"] is True

    conflicts = eng.conflict_resolution()
    assert conflicts["animation_collision_guard"] is True

    perf = eng.performance()
    assert perf["adaptive_rendering"] is True

    session = eng.start_session()
    eng.update_session(session["session_id"], {"step": 10, "draft": {"scene_name": "Ops"}})
    created = eng.create(session["session_id"])
    assert created["ok"] is True
    assert created["director_engine"]["director_engine_id"]
    assert created["scene_manager"]["scene_manager_id"]
    assert created["focus_manager"]["focus_manager_id"]
    assert created["priority_manager"]["priority_manager_id"]
    assert created["director_engine"]["generates_business_events"] is False


@pytest.mark.asyncio
async def test_api_director(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "1.54.0"
    assert body["director_engine_ready"] is True

    catalog = await client.get(f"{PREFIX}/director/catalog")
    assert catalog.status == 200
    assert (await catalog.json())["generates_business_events"] is False

    session = await client.post(f"{PREFIX}/director/sessions", json={})
    assert session.status == 201
    sid = (await session.json())["session_id"]

    create = await client.post(f"{PREFIX}/director/sessions/{sid}/create", json={})
    assert create.status == 201
    assert (await create.json())["ok"] is True

    studio = ROOT / "src" / "web" / "platform-builder" / "director" / "DirectorEngineStudio.tsx"
    page = ROOT / "src" / "web" / "platform-builder" / "pages" / "DirectorEnginePage.tsx"
    assert studio.exists()
    assert page.exists()

    docs = ROOT / "docs" / "VISUAL_DIRECTOR_ENGINE.md"
    assert docs.exists()
    knowledge = ROOT / "knowledge" / "director" / "README.md"
    assert knowledge.exists()

    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.54.0"' in manifest
    assert "32.8" in manifest
