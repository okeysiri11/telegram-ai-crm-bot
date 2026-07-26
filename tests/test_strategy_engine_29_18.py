"""Tests — Enterprise Strategy Engine (Sprint 30.3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.strategy_engine.catalogs import (
    STRATEGY_COMPONENTS,
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


def test_strategy_engine_ready():
    health = platform_builder.health()
    assert health["application_version"] == "1.65.0"
    assert health["sprint"] == "33.9"
    assert health["strategy_engine_ready"] is True
    assert health["executive_decision_ready"] is True
    assert health["enterprise_scorecard_ready"] is True
    assert health["decision_support_ready"] is True
    assert health["engines"]["strategy_engine"] == "1.0"
    assert health["engines"]["executive_registry"] == "1.0"
    assert health["engines"]["recommendation_registry"] == "1.0"
    assert health["engines"]["scorecard_engine"] == "1.0"
    assert health["engines"]["decision_support_api"] == "1.0"
    assert health["strategy"]["executes_business_logic"] is False
    assert health["strategy"]["changes_platform_state"] is False

    catalog = platform_builder.strategy.catalog()
    assert catalog["operational"] is True
    assert catalog["read_only_strategy_layer"] is True
    assert catalog["aggregates_existing_intelligence"] is True
    assert len(catalog["steps"]) == 10
    assert len(WIZARD_STEPS) == 10
    assert set(catalog["components"]) == set(STRATEGY_COMPONENTS)


def test_strategy_engine_flow_and_create():
    eng = platform_builder.strategy
    overview = eng.engine_overview()
    assert "Strategy Coordinator" in overview["components"]

    sources = eng.data_sources(action="aggregate")
    assert sources["last_aggregate"]

    strategic = eng.strategic_overview(surface="AI Overview")
    assert strategic["selected"] == "AI Overview"

    priorities = eng.strategic_priorities(category="Critical Objectives")
    assert priorities["selected"] == "Critical Objectives"

    recommendations = eng.executive_recommendations(
        recommendation_type="Scaling Recommendations"
    )
    assert recommendations["applies_changes"] is False

    scorecard = eng.enterprise_scorecard(metric="Platform Maturity")
    assert scorecard["selected"] == "Platform Maturity"
    assert scorecard["overall"] > 0

    timeline = eng.executive_timeline(segment="Strategic Roadmap")
    assert timeline["selected"] == "Strategic Roadmap"

    decisions = eng.decision_support(feature="Impact Comparison")
    assert decisions["selected"] == "Impact Comparison"

    perf = eng.performance(action="incremental_aggregation")
    assert perf["cache"]["entries"] >= 1

    session = eng.start_session()
    eng.update_session(session["session_id"], {"step": 10})
    created = eng.create(session["session_id"])
    assert created["ok"] is True
    assert created["strategy_engine"]["strategy_engine_id"]
    assert created["executive_registry"]["executive_registry_id"]
    assert created["recommendation_registry"]["recommendation_registry_id"]
    assert created["scorecard_engine"]["scorecard_engine_id"]
    assert created["decision_support_api"]["decision_support_api_id"]


@pytest.mark.asyncio
async def test_api_strategy_engine(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "1.65.0"
    assert body["strategy_engine_ready"] is True

    catalog = await client.get(f"{PREFIX}/strategy/catalog")
    assert catalog.status == 200
    assert (await catalog.json())["changes_platform_state"] is False

    session = await client.post(f"{PREFIX}/strategy/sessions", json={})
    assert session.status == 201
    sid = (await session.json())["session_id"]

    create = await client.post(f"{PREFIX}/strategy/sessions/{sid}/create", json={})
    assert create.status == 201
    assert (await create.json())["ok"] is True

    studio = ROOT / "src" / "web" / "platform-builder" / "strategy" / "StrategyStudio.tsx"
    page = ROOT / "src" / "web" / "platform-builder" / "pages" / "StrategyEnginePage.tsx"
    assert studio.exists()
    assert page.exists()

    docs = ROOT / "docs" / "ENTERPRISE_STRATEGY_ENGINE.md"
    assert docs.exists()
    knowledge = ROOT / "knowledge" / "strategy" / "README.md"
    assert knowledge.exists()

    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.65.0"' in manifest
    assert "33.6" in manifest
