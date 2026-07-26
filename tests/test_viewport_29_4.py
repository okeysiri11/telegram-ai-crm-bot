"""Tests — Viewport Engine (Sprint 29.4)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.rendering.catalogs import RENDER_LAYERS
from applications.platform_builder.rendering.engine import ViewportEngine


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


def test_viewport_culling():
    health = platform_builder.health()
    assert health["viewport_engine_ready"] is True
    assert health["layer_system_ready"] is True
    assert health["application_version"] == "1.56.0"

    vp = ViewportEngine()
    objects = [
        {"logical_id": "a", "position": {"x": 10, "y": 10}},
        {"logical_id": "b", "position": {"x": 9000, "y": 9000}},
    ]
    result = vp.cull(objects, x=0, y=0, width=100, height=100)
    assert result["visible_count"] == 1
    assert result["culled_count"] == 1
    assert result["viewport_detection"] is True
    assert result["object_culling"] is True
    assert result["lazy_rendering"] is True
    assert result["dynamic_loading"] is True


def test_viewport_and_layers_on_engine():
    eng = platform_builder.rendering
    view = eng.viewport_view(x=0, y=0, width=800, height=600, zoom=1.0)
    assert view["ready"] is True
    assert view["visible_count"] >= 0
    assert "lod" in view

    layers = eng.layer_system(zoom=1.0)
    assert list(layers["layer_names"]) == list(RENDER_LAYERS)
    assert layers["ready"] is True


@pytest.mark.asyncio
async def test_api_viewport(client):
    res = await client.get(
        f"{PREFIX}/rendering/viewport?x=0&y=0&width=800&height=600&zoom=1"
    )
    assert res.status == 200
    body = await res.json()
    assert body["object_culling"] is True

    layers = await client.get(f"{PREFIX}/rendering/layers?zoom=1")
    assert layers.status == 200
    assert (await layers.json())["ready"] is True

    docs = ROOT / "docs" / "VIEWPORT_ENGINE.md"
    assert docs.exists()
    knowledge = ROOT / "knowledge" / "viewport" / "README.md"
    assert knowledge.exists()
