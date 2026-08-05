"""Tests — Digital Twin Intelligence Engine (Sprint 30.3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.twin_intelligence.catalogs import (
    INTELLIGENCE_COMPONENTS,
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


def test_digital_twin_intelligence_ready():
    health = platform_builder.health()
    assert health["application_version"] == "1.67.0"
    assert health["sprint"] == "1.1.1"
    assert health["twin_intelligence_ready"] is True
    assert health["scenario_analysis_ready"] is True
    assert health["impact_analysis_ready"] is True
    assert health["risk_analysis_ready"] is True
    assert health["twin_recommendation_engine_ready"] is True
    assert health["engines"]["twin_intelligence_engine"] == "1.0"
    assert health["engines"]["scenario_engine"] == "1.0"
    assert health["engines"]["impact_engine"] == "1.0"
    assert health["engines"]["risk_engine"] == "1.0"
    assert health["engines"]["twin_recommendation_engine"] == "1.0"
    assert health["twin_intelligence"]["executes_business_logic"] is False
    assert health["twin_intelligence"]["changes_platform_state"] is False
    assert health["twin_intelligence"]["executes_workflows"] is False
    assert health["twin_intelligence"]["modifies_business_logic"] is False

    catalog = platform_builder.twin_intelligence.catalog()
    assert catalog["operational"] is True
    assert catalog["read_only_intelligence_layer"] is True
    assert catalog["analyzes_verified_twin_data_only"] is True
    assert len(catalog["steps"]) == 10
    assert len(WIZARD_STEPS) == 10
    assert set(catalog["components"]) == set(INTELLIGENCE_COMPONENTS)


def test_digital_twin_intelligence_flow_and_create():
    eng = platform_builder.twin_intelligence
    overview = eng.engine_overview()
    assert "Scenario Engine" in overview["components"]

    scenarios = eng.scenario_analysis(action="prepare", scenario_type="Organization Growth")
    assert scenarios["created"]["scenario_id"]

    what_if = eng.what_if_engine(action="New AI Team", input_payload={"team": "Ops AI"})
    assert what_if["simulation_input_api"] is True
    assert what_if["executes_workflows"] is False

    impact = eng.impact_analysis(dimension="Workflow Impact")
    assert impact["selected"] == "Workflow Impact"

    risk = eng.risk_analysis(category="Dependency Risks")
    assert risk["selected"] == "Dependency Risks"

    capacity = eng.capacity_analysis(dimension="AI Capacity")
    assert capacity["selected"] == "AI Capacity"

    recommendations = eng.recommendations(suggestion_type="Scaling Suggestions")
    assert recommendations["applies_changes"] is False

    comparison = eng.scenario_comparison(mode="Impact Delta")
    assert comparison["selected"] == "Impact Delta"

    perf = eng.performance(action="incremental_analysis")
    assert perf["cache"]["entries"] >= 1

    session = eng.start_session()
    eng.update_session(session["session_id"], {"step": 10})
    created = eng.create(session["session_id"])
    assert created["ok"] is True
    assert created["twin_intelligence_engine"]["twin_intelligence_engine_id"]
    assert created["scenario_engine"]["scenario_engine_id"]
    assert created["impact_engine"]["impact_engine_id"]
    assert created["risk_engine"]["risk_engine_id"]
    assert created["twin_recommendation_engine"]["twin_recommendation_engine_id"]


@pytest.mark.asyncio
async def test_api_digital_twin_intelligence(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "1.67.0"
    assert body["twin_intelligence_ready"] is True

    catalog = await client.get(f"{PREFIX}/twin-intelligence/catalog")
    assert catalog.status == 200
    assert (await catalog.json())["modifies_business_logic"] is False

    session = await client.post(f"{PREFIX}/twin-intelligence/sessions", json={})
    assert session.status == 201
    sid = (await session.json())["session_id"]

    create = await client.post(f"{PREFIX}/twin-intelligence/sessions/{sid}/create", json={})
    assert create.status == 201
    assert (await create.json())["ok"] is True

    studio = (
        ROOT
        / "src"
        / "web"
        / "platform-builder"
        / "twin-intelligence"
        / "TwinIntelligenceStudio.tsx"
    )
    page = ROOT / "src" / "web" / "platform-builder" / "pages" / "TwinIntelligencePage.tsx"
    assert studio.exists()
    assert page.exists()

    docs = ROOT / "docs" / "DIGITAL_TWIN_INTELLIGENCE.md"
    assert docs.exists()
    knowledge = ROOT / "knowledge" / "digital_twin_intelligence" / "README.md"
    assert knowledge.exists()

    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.67.0"' in manifest
    assert "33.6" in manifest
