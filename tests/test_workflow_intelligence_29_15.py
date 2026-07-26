"""Tests — Workflow Intelligence OS (Sprint 30.3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.workflow_intelligence.catalogs import (
    WORKFLOW_INTELLIGENCE_COMPONENTS,
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


def test_workflow_intelligence_ready():
    health = platform_builder.health()
    assert health["application_version"] == "1.50.0"
    assert health["sprint"] == "32.4"
    assert health["workflow_intelligence_ready"] is True
    assert health["dependency_engine_ready"] is True
    assert health["critical_path_ready"] is True
    assert health["global_process_orchestrator_ready"] is True
    assert health["engines"]["workflow_intelligence_engine"] == "1.0"
    assert health["engines"]["dependency_engine"] == "1.0"
    assert health["engines"]["critical_path_engine"] == "1.0"
    assert health["engines"]["workflow_recommendation_engine"] == "1.0"
    assert health["engines"]["workflow_analytics_api"] == "1.0"
    assert health["workflow_intelligence"]["executes_business_logic"] is False

    catalog = platform_builder.workflow_intelligence.catalog()
    assert catalog["operational"] is True
    assert catalog["orchestrates_visibility_only"] is True
    assert catalog["enterprise_scale"] is True
    assert catalog["navigation_intelligence_integration"] is True
    assert len(catalog["steps"]) == 10
    assert len(WIZARD_STEPS) == 10
    assert set(catalog["components"]) == set(WORKFLOW_INTELLIGENCE_COMPONENTS)


def test_workflow_intelligence_flow_and_create():
    eng = platform_builder.workflow_intelligence
    overview = eng.engine_overview()
    assert "Workflow Dependency Engine" in overview["components"]

    graph = eng.workflow_graph("AI Workflows")
    assert graph["selected"] == "AI Workflows"

    deps = eng.dependency_analysis()
    assert deps["count"] >= 1

    bottlenecks = eng.bottleneck_detection()
    assert "Approval Delays" in bottlenecks["findings"]

    critical = eng.critical_path()
    assert critical["critical_workflow"]
    assert critical["executes_business_logic"] is False

    resources = eng.resource_coordination()
    assert "AI Capacity" in resources["capacity"]

    recs = eng.workflow_recommendations()
    assert "Workflow Optimization" in recs["suggestions"]

    orch = eng.enterprise_orchestration("Workspace OS")
    assert orch["last_target"] == "Workspace OS"

    perf = eng.performance(action="warm_cache")
    assert perf["cache"]["workflow_entries"] >= 1

    session = eng.start_session()
    eng.update_session(session["session_id"], {"step": 10})
    created = eng.create(session["session_id"])
    assert created["ok"] is True
    assert created["workflow_intelligence_engine"]["workflow_intelligence_engine_id"]
    assert created["dependency_engine"]["dependency_engine_id"]
    assert created["critical_path_engine"]["critical_path_engine_id"]
    assert created["recommendation_engine"]["recommendation_engine_id"]
    assert created["analytics_api"]["analytics_api_id"]


@pytest.mark.asyncio
async def test_api_workflow_intelligence(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "1.50.0"
    assert body["workflow_intelligence_ready"] is True

    catalog = await client.get(f"{PREFIX}/workflow-intelligence/catalog")
    assert catalog.status == 200
    assert (await catalog.json())["executes_business_logic"] is False

    session = await client.post(f"{PREFIX}/workflow-intelligence/sessions", json={})
    assert session.status == 201
    sid = (await session.json())["session_id"]

    create = await client.post(f"{PREFIX}/workflow-intelligence/sessions/{sid}/create", json={})
    assert create.status == 201
    assert (await create.json())["ok"] is True

    studio = (
        ROOT
        / "src"
        / "web"
        / "platform-builder"
        / "workflow-intelligence"
        / "WorkflowIntelligenceStudio.tsx"
    )
    page = ROOT / "src" / "web" / "platform-builder" / "pages" / "WorkflowIntelligencePage.tsx"
    assert studio.exists()
    assert page.exists()

    docs = ROOT / "docs" / "WORKFLOW_INTELLIGENCE_OS.md"
    assert docs.exists()
    knowledge = ROOT / "knowledge" / "workflow_intelligence" / "README.md"
    assert knowledge.exists()

    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.50.0"' in manifest
    assert "32.4" in manifest
