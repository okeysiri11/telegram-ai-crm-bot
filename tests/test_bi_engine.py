"""Tests — Business Intelligence & Executive Dashboard (Sprint 6.6)."""

from __future__ import annotations

import asyncio

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.register import register_auto_marketplace_routes
from applications.auto_marketplace.business_intelligence.models import DashboardRole
from applications.auto_marketplace.business_intelligence.security import bi_security
from applications.auto_marketplace.crm.models import CRMDeal, CRMLead, CustomerProfile, DealStage, LeadSource
from applications.auto_marketplace.finance.models import FinancePayment


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_auto_marketplace_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    auto_marketplace.reset()
    yield
    auto_marketplace.reset()


def test_bi_security_roles():
    assert bi_security.authorize(DashboardRole.OWNER, "reports.all")
    assert bi_security.authorize(DashboardRole.FINANCE_MANAGER, "dashboard.finance")
    assert not bi_security.authorize(DashboardRole.DEALER, "reports.all")


@pytest.mark.asyncio
async def test_kpi_computation():
    payment = FinancePayment(deal_id="d1", customer_id="c1", amount=30000, status="completed")
    auto_marketplace.store.finance_payments.save(payment.payment_id, payment)
    kpis = auto_marketplace.bi_engine.kpi.compute_all()
    names = {k.name for k in kpis}
    assert "revenue" in names
    assert "lead_conversion" in names
    assert "vehicle_sales" in names


@pytest.mark.asyncio
async def test_executive_dashboards():
    for role in ("owner", "sales_manager", "finance_manager", "dealer", "ai_agent"):
        snapshot = await auto_marketplace.bi_engine.dashboard.get_dashboard(role)
        assert snapshot.role.value == role
        assert snapshot.widgets


@pytest.mark.asyncio
async def test_analytics_domains():
    await auto_marketplace.crm_engine.customers.create(CustomerProfile(email="bi@test.com"))
    await auto_marketplace.crm_engine.leads.create(CRMLead(customer_id="c1", source=LeadSource.WEB))
    all_data = auto_marketplace.bi_engine.analytics.all_analytics()
    assert "sales" in all_data
    assert "financial" in all_data
    assert "customer" in all_data


@pytest.mark.asyncio
async def test_forecasting():
    forecast = await auto_marketplace.bi_engine.forecasting.revenue_forecast()
    assert forecast.forecast_type == "revenue"
    assert len(forecast.predictions) >= 1
    all_fc = await auto_marketplace.bi_engine.forecasting.all_forecasts()
    assert len(all_fc) == 6


@pytest.mark.asyncio
async def test_bi_report_generation():
    report = await auto_marketplace.bi_engine.reports.generate("monthly")
    assert report.period.value == "monthly"
    export = auto_marketplace.bi_engine.reports.export(report.report_id, "pdf")
    assert export["format"] == "pdf"


@pytest.mark.asyncio
async def test_ai_insights():
    kpis = auto_marketplace.bi_engine.kpi.as_dict()
    insights = await auto_marketplace.bi_engine.insights.executive_recommendations(kpis)
    assert isinstance(insights, list)


@pytest.mark.asyncio
async def test_visualizations():
    chart = auto_marketplace.bi_engine.visualizations.revenue_chart()
    assert chart.chart_type == "bar"
    assert chart.labels


@pytest.mark.asyncio
async def test_bi_api(client: TestClient):
    resp = await client.get("/api/auto/v1/bi/metrics", headers={"Authorization": "Bearer test"})
    assert resp.status == 200

    resp = await client.get("/api/auto/v1/bi/dashboard/owner", headers={"Authorization": "Bearer test"})
    assert resp.status == 200

    resp = await client.get("/api/auto/v1/bi/kpis", headers={"Authorization": "Bearer test"})
    assert resp.status == 200

    resp = await client.get("/api/auto/v1/bi/forecast/revenue", headers={"Authorization": "Bearer test"})
    assert resp.status == 200


@pytest.mark.asyncio
async def test_dashboard_updated_event():
    received: list = []
    from events import subscribe

    subscribe("DashboardUpdatedEvent", lambda e: received.append(e))
    await auto_marketplace.bi_engine.dashboard.get_dashboard(DashboardRole.OWNER)
    await asyncio.sleep(0.05)
    assert len(received) >= 1
