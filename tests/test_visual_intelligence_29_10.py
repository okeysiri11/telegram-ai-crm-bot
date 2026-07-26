"""Tests — Visual Intelligence Engine (Sprint 30.3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.intelligence.catalogs import INTELLIGENCE_COMPONENTS, WIZARD_STEPS


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


def test_visual_intelligence_ready():
    health = platform_builder.health()
    assert health["application_version"] == "1.52.0"
    assert health["sprint"] == "32.6"
    assert health["visual_intelligence_engine_ready"] is True
    assert health["insight_engine_ready"] is True
    assert health["analytics_ready"] is True
    assert health["recommendation_engine_ready"] is True
    assert health["health_index_ready"] is True
    assert health["engines"]["visual_intelligence_engine"] == "1.0"
    assert health["engines"]["insight_engine"] == "1.0"
    assert health["engines"]["recommendation_engine"] == "1.0"
    assert health["intelligence"]["changes_business_logic"] is False
    assert health["intelligence"]["generates_business_events"] is False

    catalog = platform_builder.intelligence.catalog()
    assert catalog["operational"] is True
    assert catalog["analyzes_verified_events_only"] is True
    assert catalog["autonomous_business_decisions"] is False
    assert len(catalog["steps"]) == 10
    assert len(WIZARD_STEPS) == 10
    assert set(catalog["components"]) == set(INTELLIGENCE_COMPONENTS)


def test_analyze_and_create():
    platform_builder.simulation.emit_and_simulate("AI Activation")
    platform_builder.simulation.emit_and_simulate("Workflow Launch")
    platform_builder.simulation.emit_and_simulate("Knowledge Update")

    eng = platform_builder.intelligence
    overview = eng.engine_overview()
    assert overview["generates_business_events"] is False

    patterns = eng.pattern_detection()
    assert patterns["event_count"] >= 1
    assert "Activity Trends" in patterns["patterns"]

    anomalies = eng.anomaly_detection()
    assert anomalies["ready"] is True

    recs = eng.attention_recommendations()
    assert recs["produces_visual_recommendations_only"] is True

    health_idx = eng.visual_health_index()
    assert "Overall Platform Health" in health_idx["indices"]
    assert health_idx["changes_business_logic"] is False

    predictive = eng.predictive_foundation()
    assert predictive["autonomous_business_decisions"] is False

    session = eng.start_session()
    eng.update_session(session["session_id"], {"step": 10})
    created = eng.create(session["session_id"])
    assert created["ok"] is True
    assert created["intelligence_engine"]["intelligence_engine_id"]
    assert created["insight_registry"]["insight_registry_id"]
    assert created["analytics_registry"]["analytics_registry_id"]
    assert created["recommendation_registry"]["recommendation_registry_id"]
    assert created["intelligence_engine"]["generates_business_events"] is False


@pytest.mark.asyncio
async def test_api_intelligence(client):
    await client.post(f"{PREFIX}/simulation/emit", json={"simulation": "Task Completion"})

    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "1.52.0"
    assert body["visual_intelligence_engine_ready"] is True

    catalog = await client.get(f"{PREFIX}/intelligence/catalog")
    assert catalog.status == 200
    assert (await catalog.json())["changes_business_logic"] is False

    analyze = await client.post(f"{PREFIX}/intelligence/analyze", json={})
    assert analyze.status == 201

    session = await client.post(f"{PREFIX}/intelligence/sessions", json={})
    assert session.status == 201
    sid = (await session.json())["session_id"]

    create = await client.post(f"{PREFIX}/intelligence/sessions/{sid}/create", json={})
    assert create.status == 201
    assert (await create.json())["ok"] is True

    studio = (
        ROOT / "src" / "web" / "platform-builder" / "intelligence" / "IntelligenceEngineStudio.tsx"
    )
    page = ROOT / "src" / "web" / "platform-builder" / "pages" / "IntelligenceEnginePage.tsx"
    assert studio.exists()
    assert page.exists()

    docs = ROOT / "docs" / "VISUAL_INTELLIGENCE_ENGINE.md"
    assert docs.exists()
    knowledge = ROOT / "knowledge" / "visual_intelligence" / "README.md"
    assert knowledge.exists()

    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.52.0"' in manifest
    assert "32.6" in manifest
