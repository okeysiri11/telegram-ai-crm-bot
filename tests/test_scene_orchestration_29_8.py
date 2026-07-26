"""Tests — Scene Orchestration (Sprint 29.8)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.director.catalogs import SCENE_FEATURES, SCENE_LIFECYCLE


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


def test_scene_orchestration():
    health = platform_builder.health()
    assert health["scene_manager_ready"] is True
    assert health["application_version"] == "1.21.0"

    eng = platform_builder.director
    scenes = eng.scene_management()
    assert set(scenes["features"]) == set(SCENE_FEATURES)
    assert scenes["count"] >= 1
    assert scenes["active_scene_id"]

    scene = eng.scenes.create_scene("Department Heatmap", kind="department")
    switched = eng.scenes.switch_scene(scene["scene_id"])
    assert switched["ok"] is True
    assert switched["active_scene"]["state"] == "active"

    synced = eng.scenes.synchronize(scene["scene_id"])
    assert synced["scene"]["state"] == "synchronized"
    assert "Rendering Engine" in synced["scene"]["synced_engines"]
    assert list(synced["scene"]["lifecycle"]) == list(SCENE_LIFECYCLE)

    ui = eng.ui_dashboard()
    assert "Live Focus Indicator" in ui["surfaces"]
    assert ui["priority_timeline"]["count"] >= 1
    assert ui["generates_business_events"] is False

    live = eng.live_organization()
    assert "Executive Overview" in live["directives"]


@pytest.mark.asyncio
async def test_api_scene_orchestration(client):
    create = await client.post(
        f"{PREFIX}/director/scenes",
        json={"name": "Workflow Stage", "kind": "workflow"},
    )
    assert create.status == 201
    scene_id = (await create.json())["scene_id"]

    switch = await client.post(
        f"{PREFIX}/director/scenes/switch",
        json={"scene_id": scene_id},
    )
    assert switch.status == 200
    assert (await switch.json())["ok"] is True

    sync = await client.post(
        f"{PREFIX}/director/scenes/sync",
        json={"scene_id": scene_id},
    )
    assert sync.status == 200

    focus = await client.get(f"{PREFIX}/director/focus")
    assert focus.status == 200
    assert (await focus.json())["primary_focus"]

    docs = ROOT / "docs" / "SCENE_ORCHESTRATION.md"
    assert docs.exists()
    knowledge = ROOT / "knowledge" / "scene_management" / "README.md"
    assert knowledge.exists()
