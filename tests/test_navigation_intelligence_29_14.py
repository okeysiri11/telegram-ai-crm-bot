"""Tests — Navigation Intelligence Engine (Sprint 30.3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.navigation_intelligence.catalogs import (
    NAVIGATION_INTELLIGENCE_COMPONENTS,
    WIZARD_STEPS,
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


def test_navigation_intelligence_ready():
    health = platform_builder.health()
    assert health["application_version"] == "1.44.0"
    assert health["sprint"] == "32.3.2"
    assert health["navigation_intelligence_engine_ready"] is True
    assert health["context_navigation_ready"] is True
    assert health["smart_navigation_ready"] is True
    assert health["engines"]["navigation_intelligence_engine"] == "1.0"
    assert health["engines"]["navigation_registry"] == "1.0"
    assert health["engines"]["recommendation_api"] == "1.0"
    assert health["engines"]["context_api"] == "1.0"
    assert health["navigation_intelligence"]["executes_business_logic"] is False

    catalog = platform_builder.navigation_intelligence.catalog()
    assert catalog["operational"] is True
    assert catalog["verified_context_only"] is True
    assert catalog["workspace_os_integration"] is True
    assert catalog["command_center_integration"] is True
    assert len(catalog["steps"]) == 10
    assert len(WIZARD_STEPS) == 10
    assert set(catalog["components"]) == set(NAVIGATION_INTELLIGENCE_COMPONENTS)


def test_navigation_intelligence_flow_and_create():
    eng = platform_builder.navigation_intelligence
    overview = eng.engine_overview()
    assert "Navigation Context Engine" in overview["components"]

    graph = eng.navigation_graph("AI Graph")
    assert graph["selected"] == "AI Graph"

    ctx = eng.context_aware({"Current User Intent": "build"})
    assert ctx["determined"]["Current User Intent"] == "build"

    recs = eng.smart_recommendations()
    assert "Next Workspace" in recs["suggestions"]
    assert recs["based_on_verified_context"] is True

    history = eng.navigation_history(action="visit", location="Knowledge Center")
    assert "Knowledge Center" in history["visited_modules"]

    quick = eng.quick_access({"bookmarks": ["Ops Runbook"]})
    assert "Ops Runbook" in quick["bookmarks"]

    cross = eng.cross_platform("Marketplace")
    assert cross["last_target"] == "Marketplace"

    routing = eng.search_routing("open AI agent")
    assert any(r["route"] == "AI Agents" for r in routing["routed"])

    perf = eng.performance(action="warm_cache")
    assert perf["cache"]["nav_entries"] >= 1

    session = eng.start_session()
    eng.update_session(session["session_id"], {"step": 10})
    created = eng.create(session["session_id"])
    assert created["ok"] is True
    assert created["navigation_intelligence_engine"]["navigation_intelligence_engine_id"]
    assert created["navigation_registry"]["navigation_registry_id"]
    assert created["recommendation_api"]["recommendation_api_id"]
    assert created["context_api"]["context_api_id"]


@pytest.mark.asyncio
async def test_api_navigation_intelligence(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "1.44.0"
    assert body["navigation_intelligence_engine_ready"] is True

    catalog = await client.get(f"{PREFIX}/navigation-intelligence/catalog")
    assert catalog.status == 200
    assert (await catalog.json())["executes_business_logic"] is False

    session = await client.post(f"{PREFIX}/navigation-intelligence/sessions", json={})
    assert session.status == 201
    sid = (await session.json())["session_id"]

    create = await client.post(f"{PREFIX}/navigation-intelligence/sessions/{sid}/create", json={})
    assert create.status == 201
    assert (await create.json())["ok"] is True

    studio = (
        ROOT
        / "src"
        / "web"
        / "platform-builder"
        / "navigation-intelligence"
        / "NavigationIntelligenceStudio.tsx"
    )
    page = ROOT / "src" / "web" / "platform-builder" / "pages" / "NavigationIntelligencePage.tsx"
    assert studio.exists()
    assert page.exists()

    docs = ROOT / "docs" / "NAVIGATION_INTELLIGENCE_ENGINE.md"
    assert docs.exists()
    knowledge = ROOT / "knowledge" / "navigation" / "README.md"
    assert knowledge.exists()

    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.44.0"' in manifest
    assert "32.3.2" in manifest
