"""Tests — Enterprise Visual Analytics (Sprint 30.3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.intelligence.catalogs import HEALTH_INDICES, HEATMAP_TYPES


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


def test_visual_analytics_surfaces():
    health = platform_builder.health()
    assert health["analytics_ready"] is True
    assert health["health_index_ready"] is True
    assert health["application_version"] == "1.36.0"

    platform_builder.simulation.emit_and_simulate("Organization Creation")
    platform_builder.simulation.emit_and_simulate("Department Creation")
    platform_builder.simulation.emit_and_simulate("Document Review")

    eng = platform_builder.intelligence
    heatmaps = eng.visual_heatmaps()
    assert set(heatmaps["heatmap_names"]) == set(HEATMAP_TYPES)
    assert heatmaps["heatmaps"]["Future AI City Heatmap"]["planned"] is True

    trends = eng.trend_engine()
    assert "Growth Trends" in trends["trends"]

    health_idx = eng.visual_health_index()
    assert set(health_idx["indices"]) == set(HEALTH_INDICES)

    ui = eng.ui_dashboard()
    assert "Insight Center" in ui["surfaces"]
    assert "Heatmap Viewer" in ui["surfaces"]
    assert ui["generates_business_events"] is False

    executive = eng.executive_insights()
    assert "Daily Overview" in executive["insights"]


@pytest.mark.asyncio
async def test_api_visual_analytics(client):
    await client.post(f"{PREFIX}/simulation/emit", json={"simulation": "Knowledge Distribution"})

    health = await client.get(f"{PREFIX}/intelligence/health")
    assert health.status == 200
    body = await health.json()
    assert body["overall"] is not None

    heatmaps = await client.get(f"{PREFIX}/intelligence/heatmaps")
    assert heatmaps.status == 200

    trends = await client.get(f"{PREFIX}/intelligence/trends")
    assert trends.status == 200

    predictive = await client.get(f"{PREFIX}/intelligence/predictive")
    assert predictive.status == 200
    assert (await predictive.json())["autonomous_business_decisions"] is False

    docs = ROOT / "docs" / "ENTERPRISE_VISUAL_ANALYTICS.md"
    assert docs.exists()
    knowledge = ROOT / "knowledge" / "enterprise_analytics" / "README.md"
    assert knowledge.exists()
