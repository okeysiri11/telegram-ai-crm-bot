"""Tests — Animation Framework (Sprint 29.3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.shared.exceptions import ValidationError
from applications.platform_builder.visual_behavior.catalogs import (
    AI_CITY_APIS,
    ANIMATIONS,
    PERFORMANCE_FEATURES,
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


def test_animation_framework_and_performance():
    health = platform_builder.health()
    assert health["application_version"] == "1.32.0"
    assert health["sprint"] == "30.7"
    assert health["animation_framework_ready"] is True
    assert health["engines"]["animation_framework"] == "1.0"

    vb = platform_builder.visual_behavior
    fw = vb.animation_framework()
    assert fw["operational"] is True
    assert fw["executes_business_logic"] is False
    assert len(fw["animations"]) == len(ANIMATIONS) == 7
    for f in PERFORMANCE_FEATURES:
        assert fw["pool"][f] is True

    played = vb.play_animation("Pulse", target_id="ai_vb_1")
    assert played["ok"] is True
    assert played["pooled"] is True

    with pytest.raises(ValidationError):
        vb.play_animation("NotARealAnimation")

    perf = vb.performance()
    assert perf["optimized"] is True
    assert perf["target_fps"] == 60
    assert perf["lazy_rendering"] is True
    assert perf["viewport_culling"] is True

    city = vb.ai_city_apis("ai_vb_1")
    for name in AI_CITY_APIS:
        assert name in city["apis"]
    assert city["apis"]["Movement API"]["planned"] is True
    assert city["apis"]["Behavior API"]["ready"] is True


@pytest.mark.asyncio
async def test_api_animation_framework(client):
    anims = await client.get(f"{PREFIX}/visual-behavior/animations")
    assert anims.status == 200

    play = await client.post(
        f"{PREFIX}/visual-behavior/animations/play",
        json={"animation": "Glow", "target_id": "task_vb"},
    )
    assert play.status == 200

    wait = await client.get(f"{PREFIX}/visual-behavior/wait-experience")
    assert wait.status == 200
    body = await wait.json()
    assert body["fake_processing"] is False

    perf = await client.get(f"{PREFIX}/visual-behavior/performance")
    assert perf.status == 200

    city = await client.get(f"{PREFIX}/visual-behavior/ai-city-apis?logical_id=ai_vb_1")
    assert city.status == 200

    tr = await client.post(
        f"{PREFIX}/visual-behavior/transitions/run",
        json={"logical_id": "ai_vb_1", "to_behavior": "Working"},
    )
    assert tr.status == 200


def test_docs_animation_framework_29_3():
    docs = (ROOT / "docs" / "ANIMATION_FRAMEWORK.md").read_text()
    for key in ("Animation Pool", "No fake processing", "Behavior API", "Viewport Rendering"):
        assert key in docs
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"animation_framework": "1.0"' in manifest
    assert '"transition_engine": "1.0"' in manifest
    assert '"visual_behavior_engine": "1.0"' in manifest
