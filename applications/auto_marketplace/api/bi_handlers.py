# BI API handlers — Sprint 6.6.

from __future__ import annotations

from aiohttp import web

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.middleware import json_response
from applications.auto_marketplace.business_intelligence.models import DashboardRole
from applications.auto_marketplace.shared.exceptions import AuthorizationError


def _check_bi_perm(request: web.Request, permission: str = "bi.read") -> None:
    principal = request.get("principal") or {}
    role = principal.get("role", DashboardRole.ADMINISTRATOR.value)
    if not auto_marketplace.bi_engine.security.authorize(role, permission):
        raise AuthorizationError(f"Permission denied: {permission}")


async def bi_metrics_handler(_request: web.Request) -> web.Response:
    return json_response(auto_marketplace.bi_engine.metrics())


async def dashboard_handler(request: web.Request) -> web.Response:
    _check_bi_perm(request, "bi.read")
    role = request.match_info.get("role") or request.query.get("role", DashboardRole.OWNER.value)
    snapshot = await auto_marketplace.bi_engine.dashboard.get_dashboard(role)
    return json_response(snapshot.to_dict())


async def kpi_handler(_request: web.Request) -> web.Response:
    _check_bi_perm(_request, "kpi.all")
    return json_response({"items": [k.to_dict() for k in auto_marketplace.bi_engine.kpi.compute_all()]})


async def kpi_single_handler(request: web.Request) -> web.Response:
    _check_bi_perm(request, "kpi.all")
    kpi = auto_marketplace.bi_engine.kpi.get_kpi(request.match_info["name"])
    if kpi is None:
        return json_response({"error": "KPI not found"}, status=404)
    return json_response(kpi.to_dict())


async def analytics_handler(request: web.Request) -> web.Response:
    _check_bi_perm(request, "analytics.all")
    domain = request.match_info.get("domain", "")
    engine = auto_marketplace.bi_engine.analytics
    mapping = {
        "sales": engine.sales_analytics,
        "financial": engine.financial_analytics,
        "customer": engine.customer_analytics,
        "inventory": engine.inventory_analytics,
        "marketing": engine.marketing_analytics,
        "dealer": engine.dealer_analytics,
        "workflow": engine.workflow_analytics,
        "agent": engine.agent_analytics,
    }
    if domain and domain in mapping:
        return json_response(mapping[domain]())
    return json_response(engine.all_analytics())


async def forecast_handler(request: web.Request) -> web.Response:
    _check_bi_perm(request, "forecast.all")
    forecast_type = request.match_info.get("type", "sales")
    period_days = int(request.query.get("days", "30"))
    svc = auto_marketplace.bi_engine.forecasting
    methods = {
        "sales": svc.sales_forecast,
        "revenue": svc.revenue_forecast,
        "inventory": svc.inventory_forecast,
        "demand": svc.demand_forecast,
        "cashflow": svc.cashflow_forecast,
        "growth": svc.growth_forecast,
    }
    if forecast_type == "all":
        results = await svc.all_forecasts(period_days=period_days)
        return json_response({k: v.to_dict() for k, v in results.items()})
    method = methods.get(forecast_type, svc.sales_forecast)
    result = await method(period_days=period_days)
    return json_response(result.to_dict())


async def generate_report_handler(request: web.Request) -> web.Response:
    _check_bi_perm(request, "reports.all")
    period = request.query.get("period", "daily")
    report = await auto_marketplace.bi_engine.reports.generate(period)
    return json_response(report.to_dict(), status=201)


async def export_report_handler(request: web.Request) -> web.Response:
    _check_bi_perm(request, "reports.all")
    fmt = request.query.get("format", "pdf")
    result = auto_marketplace.bi_engine.reports.export(request.match_info["report_id"], fmt)
    return json_response(result)


async def insights_handler(_request: web.Request) -> web.Response:
    _check_bi_perm(_request, "insights.generate")
    kpis = auto_marketplace.bi_engine.kpi.as_dict()
    analytics = auto_marketplace.bi_engine.analytics.all_analytics()
    insights_svc = auto_marketplace.bi_engine.insights
    all_insights = []
    all_insights.extend(await insights_svc.detect_anomalies({"revenue": kpis.get("revenue", 0), "revenue_target": 50000}))
    all_insights.extend(await insights_svc.detect_opportunities({"hot_leads": analytics["sales"].get("leads_by_source", {}).get("web", 0)}))
    all_insights.extend(await insights_svc.detect_risks({"at_risk_customers": 0}))
    all_insights.extend(await insights_svc.executive_recommendations(kpis))
    for ins in all_insights:
        auto_marketplace.store.bi_insights.save(ins.insight_id, ins)
    return json_response({"items": [i.to_dict() for i in all_insights]})


async def statistics_handler(_request: web.Request) -> web.Response:
    _check_bi_perm(_request, "bi.read")
    return json_response(auto_marketplace.bi_engine.statistics.summary())


async def visualizations_handler(request: web.Request) -> web.Response:
    _check_bi_perm(request, "bi.read")
    chart_type = request.match_info.get("type", "revenue")
    viz = auto_marketplace.bi_engine.visualizations
    charts = {
        "revenue": viz.revenue_chart,
        "pipeline": viz.pipeline_chart,
        "leads": viz.lead_source_chart,
    }
    chart = charts.get(chart_type, viz.revenue_chart)()
    return json_response(chart.to_dict())
