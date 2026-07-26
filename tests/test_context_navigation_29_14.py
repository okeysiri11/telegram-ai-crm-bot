"""Tests — Context Navigation Platform (Sprint 30.3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.navigation_intelligence.catalogs import (
    CROSS_PLATFORM_TARGETS,
    RECOMMENDATION_TYPES,
    SEARCH_ROUTES,
    UI_SURFACES,
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


def test_context_navigation_surfaces():
    health = platform_builder.health()
    assert health["context_navigation_ready"] is True
    assert health["application_version"] == "1.57.0"

    eng = platform_builder.navigation_intelligence
    recs = eng.smart_recommendations()
    assert set(recs["types"]) == set(RECOMMENDATION_TYPES)

    cross = eng.cross_platform()
    assert set(cross["targets"]) == set(CROSS_PLATFORM_TARGETS)

    routing = eng.search_routing()
    assert set(routing["routes"]) == set(SEARCH_ROUTES)

    ui = eng.ui_dashboard()
    assert set(ui["surfaces"]) == set(UI_SURFACES)
    assert "Recommendation Sidebar" in ui["surfaces"]
    assert ui["executes_business_logic"] is False


@pytest.mark.asyncio
async def test_api_context_navigation(client):
    ctx = await client.patch(
        f"{PREFIX}/navigation-intelligence/context",
        json={"Current Project": "nav_platform"},
    )
    assert ctx.status == 200
    assert (await ctx.json())["determined"]["Current Project"] == "nav_platform"

    recs = await client.get(f"{PREFIX}/navigation-intelligence/recommendations")
    assert recs.status == 200
    assert (await recs.json())["based_on_verified_context"] is True

    history = await client.post(
        f"{PREFIX}/navigation-intelligence/history",
        json={"action": "pin", "location": "Analytics"},
    )
    assert history.status == 201
    assert "Analytics" in (await history.json())["pinned_locations"]

    routing = await client.post(
        f"{PREFIX}/navigation-intelligence/search-routing",
        json={"query": "marketplace apps"},
    )
    assert routing.status == 201
    assert any(r["route"] == "Marketplace" for r in (await routing.json())["routed"])

    ui = await client.get(f"{PREFIX}/navigation-intelligence/ui")
    assert ui.status == 200

    docs = ROOT / "docs" / "CONTEXT_NAVIGATION_PLATFORM.md"
    assert docs.exists()
    knowledge = ROOT / "knowledge" / "context_navigation" / "README.md"
    assert knowledge.exists()
