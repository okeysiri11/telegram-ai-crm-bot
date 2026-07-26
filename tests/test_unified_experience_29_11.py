"""Tests — Unified Enterprise Experience (Sprint 29.15)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.experience.catalogs import (
    ACCESSIBILITY_FEATURES,
    UNIFIED_SUBSYSTEMS,
    USER_CONTEXTS,
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


def test_unified_experience_surfaces():
    health = platform_builder.health()
    assert health["unified_ux_ready"] is True
    assert health["adaptive_interface_ready"] is True
    assert health["accessibility_operational"] is True
    assert health["application_version"] == "1.22.0"

    eng = platform_builder.experience
    unified = eng.unified_experience()
    assert set(unified["subsystem_names"]) == set(UNIFIED_SUBSYSTEMS)

    for ctx in USER_CONTEXTS:
        result = eng.user_context(ctx)
        assert result["active_context"] == ctx
        assert result["profile"]

    ui = eng.ui_dashboard()
    assert "Experience Center" in ui["surfaces"]
    assert "UX Diagnostics" in ui["surfaces"]
    assert "Adaptive UI Panel" in ui["surfaces"]
    assert ui["executes_business_logic"] is False

    a11y = eng.accessibility({"Reduced Motion": True})
    assert set(a11y["feature_names"]) == set(ACCESSIBILITY_FEATURES)


@pytest.mark.asyncio
async def test_api_unified_experience(client):
    unified = await client.get(f"{PREFIX}/experience/unified")
    assert unified.status == 200
    assert (await unified.json())["seamless"] is True

    ctx = await client.post(f"{PREFIX}/experience/context", json={"context": "Developer Context"})
    assert ctx.status == 201
    assert (await ctx.json())["active_context"] == "Developer Context"

    adaptive = await client.get(f"{PREFIX}/experience/adaptive")
    assert adaptive.status == 200

    cognitive = await client.get(f"{PREFIX}/experience/cognitive")
    assert cognitive.status == 200

    a11y = await client.get(f"{PREFIX}/experience/accessibility")
    assert a11y.status == 200

    ui = await client.get(f"{PREFIX}/experience/ui")
    assert ui.status == 200

    docs = ROOT / "docs" / "UNIFIED_ENTERPRISE_EXPERIENCE.md"
    assert docs.exists()
    knowledge = ROOT / "knowledge" / "unified_ux" / "README.md"
    assert knowledge.exists()
