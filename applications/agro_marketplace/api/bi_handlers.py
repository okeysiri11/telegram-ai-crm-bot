# Analytics / Dashboard / Forecast / KPI / Reports / Insights API — Sprint 8.6.

from __future__ import annotations

from aiohttp import web

from applications.agro_marketplace import agro_marketplace
from applications.agro_marketplace.analytics.models import (
    DashboardKind,
    KPIName,
    MetricPoint,
    SimulationScenario,
)
from applications.agro_marketplace.api.middleware import error_response, json_response
from applications.agro_marketplace.shared.exceptions import NotFoundError, ValidationError


async def analytics_health_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "analytics_engine": agro_marketplace.config.analytics_engine,
            "application_version": agro_marketplace.config.application_version,
            "bi": agro_marketplace.business_intelligence.health(),
            "metrics": agro_marketplace.analytics_engine.metrics(),
        }
    )


async def analytics_domains_handler(_request: web.Request) -> web.Response:
    return json_response(agro_marketplace.analytics_engine.all_domains())


async def analytics_domain_handler(request: web.Request) -> web.Response:
    domain = request.match_info["domain"]
    result = agro_marketplace.analytics_engine.domain(domain)
    if result.get("error"):
        return error_response(result["error"], status=404)
    return json_response(result)


async def dashboard_list_kinds_handler(_request: web.Request) -> web.Response:
    return json_response({"items": [k.value for k in DashboardKind]})


async def dashboard_build_handler(request: web.Request) -> web.Response:
    kind = request.match_info["kind"]
    subject_id = request.query.get("subject_id", "")
    try:
        dash = await agro_marketplace.business_intelligence.role_dashboard(kind, subject_id=subject_id)
        return json_response(dash)
    except ValueError:
        return error_response(f"unknown dashboard kind: {kind}", status=400)


async def dashboard_executive_handler(_request: web.Request) -> web.Response:
    result = await agro_marketplace.business_intelligence.refresh_executive()
    return json_response(result)


async def forecast_suite_handler(request: web.Request) -> web.Response:
    data = {}
    try:
        data = await request.json()
    except Exception:
        data = {}
    subject = data.get("subject") or request.query.get("subject", "maize")
    region = data.get("region") or request.query.get("region", "")
    result = await agro_marketplace.business_intelligence.forecasting_suite(subject, region=region)
    return json_response(result)


async def forecast_bi_handler(request: web.Request) -> web.Response:
    kind = request.match_info.get("kind") or request.path.rstrip("/").split("/")[-1]
    data = {}
    try:
        data = await request.json()
    except Exception:
        data = {}
    subject = data.get("subject") or request.query.get("subject", "maize")
    region = data.get("region") or request.query.get("region", "")
    engine = agro_marketplace.business_intelligence.forecasting
    mapping = {
        "storage": engine.forecast_storage,
        "export": engine.forecast_export,
        "revenue": engine.forecast_revenue,
        "market_trend": engine.forecast_market_trend,
        "demand": engine.forecast_demand,
        "supply": engine.forecast_supply,
        "price": engine.forecast_price,
        "harvest": engine.forecast_harvest,
    }
    fn = mapping.get(kind)
    if fn is None:
        return error_response(f"unknown forecast kind: {kind}", status=404)
    result = await fn(subject, region=region)
    return json_response(result.to_dict())


async def kpi_calculate_handler(_request: web.Request) -> web.Response:
    items = await agro_marketplace.analytics_engine.kpi.calculate_all()
    return json_response({"items": [i.to_dict() for i in items]})


async def kpi_get_handler(request: web.Request) -> web.Response:
    name = request.match_info["name"]
    try:
        snap = await agro_marketplace.analytics_engine.kpi.calculate(KPIName(name))
        return json_response(snap.to_dict())
    except ValueError:
        return error_response(f"unknown kpi: {name}", status=404)


async def kpi_list_handler(_request: web.Request) -> web.Response:
    items = agro_marketplace.analytics_engine.kpi.list_snapshots()
    return json_response({"items": [i.to_dict() for i in items]})


async def reports_executive_handler(request: web.Request) -> web.Response:
    data = {}
    try:
        data = await request.json()
    except Exception:
        data = {}
    report = await agro_marketplace.analytics_engine.executive.build_executive_report(
        title=data.get("title", "Executive Agro Brief")
    )
    return json_response(report.to_dict(), status=201)


async def reports_list_handler(request: web.Request) -> web.Response:
    items = agro_marketplace.analytics_engine.reporting.list_reports(
        report_type=request.query.get("type") or None
    )
    return json_response({"items": [r.to_dict() for r in items]})


async def insights_generate_handler(_request: web.Request) -> web.Response:
    metrics = agro_marketplace.analytics_engine.kpi.latest_map()
    if not metrics:
        snaps = await agro_marketplace.analytics_engine.kpi.calculate_all()
        metrics = {s.name.value: s.value for s in snaps}
    items = await agro_marketplace.analytics_engine.insights.generate(metrics=metrics)
    return json_response({"items": [i.to_dict() for i in items]})


async def insights_list_handler(_request: web.Request) -> web.Response:
    return json_response(
        {"items": [i.to_dict() for i in agro_marketplace.analytics_engine.insights.list_insights()]}
    )


async def anomalies_detect_handler(_request: web.Request) -> web.Response:
    metrics = agro_marketplace.analytics_engine.kpi.latest_map()
    if not metrics:
        snaps = await agro_marketplace.analytics_engine.kpi.calculate_all()
        metrics = {s.name.value: s.value for s in snaps}
    items = await agro_marketplace.analytics_engine.insights.detect_anomalies(metrics)
    return json_response({"items": [a.to_dict() for a in items]})


async def simulation_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        scenario = agro_marketplace.analytics_engine.simulation.create(
            SimulationScenario(
                name=data.get("name", ""),
                description=data.get("description", ""),
                inputs=dict(data.get("inputs", {})),
            )
        )
        return json_response(scenario.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def simulation_run_handler(request: web.Request) -> web.Response:
    try:
        scenario = await agro_marketplace.analytics_engine.simulation.run(
            request.match_info["scenario_id"]
        )
        return json_response(scenario.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def simulation_quick_handler(request: web.Request) -> web.Response:
    data = await request.json()
    result = await agro_marketplace.business_intelligence.run_simulation(
        data.get("name", "scenario"),
        dict(data.get("inputs", {})),
    )
    return json_response(result, status=201)


async def metrics_record_handler(request: web.Request) -> web.Response:
    data = await request.json()
    point = agro_marketplace.analytics_engine.metrics_svc.record(
        MetricPoint(
            name=data.get("name", ""),
            value=float(data.get("value", 0)),
            unit=data.get("unit", ""),
            domain=data.get("domain", ""),
            dimensions=dict(data.get("dimensions", {})),
        )
    )
    return json_response(point.to_dict(), status=201)
