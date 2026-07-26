"""Tests — Visual LOD Engine (Sprint 29.4)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.rendering.catalogs import LOD_LEVELS, LOD_OBJECT_TYPES
from applications.platform_builder.rendering.engine import LODEngine


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


def test_lod_levels_by_zoom():
    lod = LODEngine()
    assert lod.level_for_zoom(0.1)["id"] == "L0"
    assert lod.level_for_zoom(0.4)["id"] == "L1"
    assert lod.level_for_zoom(0.6)["id"] == "L2"
    assert lod.level_for_zoom(0.8)["id"] == "L3"
    assert lod.level_for_zoom(1.0)["id"] == "L4"
    assert len(LOD_LEVELS) == 5
    assert "organization" in LOD_OBJECT_TYPES["L0"]
    assert "document" in LOD_OBJECT_TYPES["L4"]


def test_lod_filters_scene():
    health = platform_builder.health()
    assert health["visual_lod_engine_ready"] is True
    assert health["application_version"] == "1.19.0"

    view_l0 = platform_builder.rendering.lod_view(0.1)
    assert view_l0["lod"]["id"] == "L0"
    assert all(o["object_type"] == "organization" for o in view_l0["objects"])
    assert view_l0["auto_detail_by_zoom"] is True

    view_l1 = platform_builder.rendering.lod_view(0.4)
    assert view_l1["lod"]["id"] == "L1"
    assert set(view_l1["allowed_types"]) <= {"organization", "department"}

    view_l4 = platform_builder.rendering.lod_view(1.2)
    assert view_l4["lod"]["id"] == "L4"
    assert view_l4["output_count"] >= view_l0["output_count"]


@pytest.mark.asyncio
async def test_api_lod(client):
    res = await client.get(f"{PREFIX}/rendering/lod?zoom=0.4")
    assert res.status == 200
    body = await res.json()
    assert body["lod"]["id"] == "L1"
    assert body["ready"] is True

    docs = ROOT / "docs" / "VISUAL_LOD_ENGINE.md"
    assert docs.exists()
    knowledge = ROOT / "knowledge" / "lod" / "README.md"
    assert knowledge.exists()
