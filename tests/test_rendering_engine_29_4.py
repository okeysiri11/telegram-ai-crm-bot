"""Tests — Visual Rendering Engine (Sprint 29.4)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.rendering.catalogs import RENDERER_CAPABILITIES, WIZARD_STEPS


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


def test_rendering_engine_ready():
    health = platform_builder.health()
    assert health["application_version"] == "1.46.0"
    assert health["sprint"] == "32.3.4"
    assert health["rendering_engine_ready"] is True
    assert health["visual_lod_engine_ready"] is True
    assert health["viewport_engine_ready"] is True
    assert health["layer_system_ready"] is True
    assert health["render_performance_monitor_ready"] is True
    assert health["engines"]["rendering_engine"] == "1.0"
    assert health["engines"]["visual_lod_engine"] == "1.0"
    assert health["engines"]["viewport_engine"] == "1.0"
    assert health["engines"]["layer_system"] == "1.0"
    assert health["rendering"]["executes_business_logic"] is False
    assert health["rendering"]["gpu_friendly"] is True

    catalog = platform_builder.rendering.catalog()
    assert catalog["operational"] is True
    assert catalog["executes_business_logic"] is False
    assert catalog["independent_from_business_logic"] is True
    assert catalog["gpu_friendly"] is True
    assert len(catalog["steps"]) == 10
    assert len(WIZARD_STEPS) == 10
    assert set(catalog["renderer_capabilities"]) == set(RENDERER_CAPABILITIES)


def test_renderer_layers_priority_perf_create():
    eng = platform_builder.rendering
    renderer = eng.renderer(zoom=1.0)
    assert renderer["ready"] is True
    assert renderer["object_pool"]["size"] > 0
    assert len(renderer["render_queue"]) > 0
    assert renderer["layer_rendering"] is True
    assert renderer["executes_business_logic"] is False

    layers = eng.layer_system(zoom=1.0)
    assert layers["ready"] is True
    assert "AI" in layers["layer_names"]
    assert "Background" in layers["counts"]

    priorities = eng.priorities()
    assert priorities["ready"] is True
    assert "high" in priorities["counts"]

    anim = eng.animation_optimization()
    assert anim["frame_limit_fps"] == 60
    assert anim["smooth_transitions"] is True

    live = eng.live_organization_support()
    assert "Current Activity" in live["surfaces"]

    city = eng.ai_city_foundation()
    assert "Tile Rendering" in city["interfaces"]

    perf = eng.performance()
    assert "FPS Monitor" in perf["metrics"]
    assert perf["gpu_friendly"] is True

    sync = eng.sync_from_sources()
    assert sync["executes_business_logic"] is False
    assert "Visual Event Bus" in sync["sources"]

    session = eng.start_session()
    eng.update_session(session["session_id"], {"step": 10, "draft": {"zoom": 1.0}})
    created = eng.create(session["session_id"])
    assert created["ok"] is True
    assert created["rendering_engine"]["rendering_engine_id"]
    assert created["lod_engine"]["lod_engine_id"]
    assert created["viewport_engine"]["viewport_engine_id"]
    assert created["layer_system"]["layer_system_id"]
    assert created["rendering_engine"]["executes_business_logic"] is False


@pytest.mark.asyncio
async def test_api_rendering(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "1.46.0"
    assert body["rendering_engine_ready"] is True

    catalog = await client.get(f"{PREFIX}/rendering/catalog")
    assert catalog.status == 200
    assert (await catalog.json())["executes_business_logic"] is False

    renderer = await client.get(f"{PREFIX}/rendering/renderer?zoom=1")
    assert renderer.status == 200
    assert (await renderer.json())["ready"] is True

    session = await client.post(f"{PREFIX}/rendering/sessions", json={})
    assert session.status == 201
    sid = (await session.json())["session_id"]

    create = await client.post(f"{PREFIX}/rendering/sessions/{sid}/create", json={})
    assert create.status == 201
    assert (await create.json())["ok"] is True

    studio = ROOT / "src" / "web" / "platform-builder" / "rendering" / "RenderingEngineStudio.tsx"
    page = ROOT / "src" / "web" / "platform-builder" / "pages" / "RenderingEnginePage.tsx"
    assert studio.exists()
    assert page.exists()

    docs = ROOT / "docs" / "VISUAL_RENDERING_ENGINE.md"
    assert docs.exists()
    knowledge = ROOT / "knowledge" / "rendering" / "README.md"
    assert knowledge.exists()

    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.46.0"' in manifest
    assert "32.3.4" in manifest
