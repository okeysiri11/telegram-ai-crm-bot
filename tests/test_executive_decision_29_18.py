"""Tests — Executive Decision Intelligence (Sprint 29.19)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.strategy_engine.catalogs import (
    DECISION_SUPPORT_FEATURES,
    SCORECARD_METRICS,
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


def test_executive_decision_surfaces():
    eng = platform_builder.strategy
    scorecard = eng.enterprise_scorecard()
    assert set(scorecard["metrics"]) == set(SCORECARD_METRICS)
    assert scorecard["read_only"] is True

    decisions = eng.decision_support()
    assert set(decisions["features"]) == set(DECISION_SUPPORT_FEATURES)
    assert decisions["executes_business_logic"] is False

    ui = eng.ui_dashboard()
    assert set(ui["surfaces"]) == set(UI_SURFACES)
    assert ui["read_only_strategy_layer"] is True


@pytest.mark.asyncio
async def test_api_executive_decision(client):
    scorecard = await client.get(f"{PREFIX}/strategy/scorecard")
    assert scorecard.status == 200
    assert (await scorecard.json())["overall"] > 0

    decisions = await client.post(
        f"{PREFIX}/strategy/decisions",
        json={"feature": "Risk Comparison"},
    )
    assert decisions.status == 201
    assert (await decisions.json())["selected"] == "Risk Comparison"

    timeline = await client.get(f"{PREFIX}/strategy/timeline")
    assert timeline.status == 200

    priorities = await client.get(f"{PREFIX}/strategy/priorities")
    assert priorities.status == 200

    recommendations = await client.get(f"{PREFIX}/strategy/recommendations")
    assert recommendations.status == 200

    ui = await client.get(f"{PREFIX}/strategy/ui")
    assert ui.status == 200

    docs = ROOT / "docs" / "EXECUTIVE_DECISION_INTELLIGENCE.md"
    assert docs.exists()
    knowledge = ROOT / "knowledge" / "executive_decisions" / "README.md"
    assert knowledge.exists()
