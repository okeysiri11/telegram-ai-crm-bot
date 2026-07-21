"""Tests — Agricultural Analytics, Forecasting & BI (Sprint 8.6)."""

from __future__ import annotations

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.agro_marketplace import agro_marketplace
from applications.agro_marketplace.analytics.models import DashboardKind, KPIName, SimulationScenario
from applications.agro_marketplace.api.register import register_agro_marketplace_routes


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_agro_marketplace_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    agro_marketplace.reset()
    yield
    agro_marketplace.reset()


def test_version_and_domains():
    health = agro_marketplace.health()
    assert health["application_version"] == "1.5.0-alpha"
    assert health["analytics_engine"] == "1.0"
    domains = agro_marketplace.analytics_engine.all_domains()
    assert set(domains) >= {
        "sales",
        "inventory",
        "harvest",
        "crop",
        "demand",
        "supply",
        "pricing",
        "export",
        "customer",
        "regional",
    }


@pytest.mark.asyncio
async def test_kpi_and_executive_dashboard():
    kpis = await agro_marketplace.analytics_engine.kpi.calculate_all()
    assert len(kpis) == 10
    names = {k.name for k in kpis}
    assert KPIName.REVENUE in names
    assert KPIName.AI_PERFORMANCE in names

    dash = await agro_marketplace.dashboards.executive()
    assert dash.kind == DashboardKind.EXECUTIVE
    assert dash.kpis
    assert dash.widgets

    report = await agro_marketplace.analytics_engine.executive.build_executive_report()
    assert report.report_id
    assert report.kpis


@pytest.mark.asyncio
async def test_forecasting_suite_and_insights():
    suite = await agro_marketplace.business_intelligence.forecasting_suite("maize", region="Rift")
    assert set(suite) >= {
        "demand",
        "supply",
        "price",
        "harvest",
        "storage",
        "export",
        "revenue",
        "market_trend",
    }
    metrics = agro_marketplace.analytics_engine.kpi.latest_map()
    insights = await agro_marketplace.analytics_engine.insights.generate(metrics=metrics)
    assert insights
    anomalies = await agro_marketplace.analytics_engine.insights.detect_anomalies(
        {"revenue": 1000.0, "order_volume": 2.0}
    )
    assert isinstance(anomalies, list)


@pytest.mark.asyncio
async def test_role_dashboards_and_simulation():
    for kind in DashboardKind:
        dash = await agro_marketplace.dashboards.build(kind)
        assert dash.kind == kind
        assert dash.title

    scenario = agro_marketplace.analytics_engine.simulation.create(
        SimulationScenario(
            name="demand_up",
            inputs={"base_revenue": 20000, "price_change_pct": 0, "demand_change_pct": 10},
        )
    )
    done = await agro_marketplace.analytics_engine.simulation.run(scenario.scenario_id)
    assert done.status == "completed"
    assert done.results["projected_revenue"] > 20000


@pytest.mark.asyncio
async def test_api_analytics_and_dashboards(client: TestClient):
    health = await client.get("/api/agro/v1/analytics/health")
    assert health.status == 200
    body = await health.json()
    assert body["analytics_engine"] == "1.0"
    assert body["application_version"] == "1.5.0-alpha"

    sales = await client.get("/api/agro/v1/analytics/domains/sales")
    assert sales.status == 200

    kpi = await client.post("/api/agro/v1/kpi/calculate")
    assert kpi.status == 200
    assert len((await kpi.json())["items"]) == 10

    exec_dash = await client.post("/api/agro/v1/dashboards/executive")
    assert exec_dash.status == 200
    data = await exec_dash.json()
    assert "dashboard" in data or data.get("kind") == "executive" or "report" in data

    suite = await client.post("/api/agro/v1/bi/forecast/suite", json={"subject": "wheat"})
    assert suite.status == 200
    assert "price" in await suite.json()

    report = await client.post("/api/agro/v1/reports/executive", json={"title": "Q Brief"})
    assert report.status == 201

    insights = await client.post("/api/agro/v1/insights/generate")
    assert insights.status == 200
