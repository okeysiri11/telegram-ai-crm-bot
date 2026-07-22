"""API handlers — Executive Command Center (Sprint 12.3)."""

from __future__ import annotations

from aiohttp import web

from applications.executive_center import executive_center
from applications.executive_center.api.middleware import json_response
from applications.executive_center.shared.exceptions import NotFoundError, ValidationError


async def _read_json(request: web.Request) -> dict:
    try:
        data = await request.json()
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _handle_error(exc: Exception) -> web.Response:
    if isinstance(exc, NotFoundError):
        return json_response({"error": str(exc)}, status=404)
    if isinstance(exc, ValidationError):
        return json_response({"error": str(exc)}, status=400)
    return json_response({"error": str(exc)}, status=500)


async def health_handler(request: web.Request) -> web.Response:
    return json_response(executive_center.health())


async def bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(executive_center.bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def dashboard_handler(request: web.Request) -> web.Response:
    try:
        dash = executive_center.dashboard
        if request.method == "GET":
            dtype = request.rel_url.query.get("type", "global")
            if dtype == "all":
                return json_response(dash.all_dashboards())
            if dtype == "finance":
                return json_response(dash.finance_dashboard())
            if dtype == "operations":
                return json_response(dash.operations_dashboard())
            if dtype == "ai":
                return json_response(dash.ai_dashboard())
            if dtype == "company":
                return json_response(dash.company_dashboard(request.rel_url.query.get("company_id", "")))
            if dtype == "project":
                return json_response(dash.project_dashboard(request.rel_url.query.get("project_id", "")))
            if dtype == "department":
                return json_response(dash.department_dashboard(request.rel_url.query.get("department_id", "")))
            return json_response(dash.global_dashboard())
        body = await _read_json(request)
        action = body.get("action", "kpi")
        if action == "metric":
            return json_response(dash.record_metric(name=body.get("name", ""), value=float(body.get("value", 0)), tags=body.get("tags")), status=201)
        if action == "activity":
            return json_response(dash.activity(actor=body.get("actor", ""), action=body.get("event", body.get("activity_action", "")), detail=body.get("detail", "")), status=201)
        return json_response(
            dash.publish_kpi(name=body.get("name", ""), value=float(body.get("value", 0)), unit=body.get("unit", ""), scope=body.get("scope", "global")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def twins_handler(request: web.Request) -> web.Response:
    try:
        twins = executive_center.twins
        if request.method == "GET":
            return json_response({"twins": twins.list_twins(twin_type=request.rel_url.query.get("type")), "status": twins.status()})
        body = await _read_json(request)
        action = body.get("action", "create")
        if action == "sync":
            return json_response(twins.live_sync(body.get("twin_id", ""), state=body.get("state") or {}))
        if action == "sync_all":
            return json_response(twins.sync_all())
        if action == "history":
            return json_response({"history": twins.state_history(body.get("twin_id", ""))})
        if action == "time_travel":
            return json_response(twins.time_travel(body.get("twin_id", ""), snapshot_id=body.get("snapshot_id", "")))
        if action == "bootstrap":
            return json_response({"created": twins.ensure_ecosystem_twins()}, status=201)
        return json_response(
            twins.create(
                twin_type=body.get("twin_type", "application"),
                name=body.get("name", ""),
                source_id=body.get("source_id", ""),
                state=body.get("state"),
                metadata=body.get("metadata"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def monitoring_handler(request: web.Request) -> web.Response:
    try:
        mon = executive_center.monitoring
        if request.method == "GET":
            return json_response(mon.overview())
        body = await _read_json(request)
        action = body.get("action", "sample")
        if action == "health_check":
            return json_response(mon.health_check(target=body.get("target", ""), ok=bool(body.get("ok", True)), detail=body.get("detail", "")), status=201)
        return json_response(
            mon.sample(
                cpu_pct=float(body.get("cpu_pct", 32)),
                ram_pct=float(body.get("ram_pct", 48)),
                gpu_pct=float(body.get("gpu_pct", 12)),
                storage_pct=float(body.get("storage_pct", 55)),
                network_mbps=float(body.get("network_mbps", 120)),
                containers=int(body.get("containers", 8)),
                services_up=int(body.get("services_up", 12)),
                agents_active=int(body.get("agents_active", 6)),
                queue_depth=int(body.get("queue_depth", 3)),
                workflows_running=int(body.get("workflows_running", 2)),
                api_latency_ms=float(body.get("api_latency_ms", 45)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ai_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            executive_center.ai.assist(agent=body.get("agent", "ceo_assistant"), query=body.get("query", ""), context=body.get("context")),
        )
    except Exception as exc:
        return _handle_error(exc)


async def analytics_handler(request: web.Request) -> web.Response:
    try:
        analytics = executive_center.analytics
        if request.method == "GET":
            return json_response(analytics.all_domains())
        body = await _read_json(request)
        return json_response(analytics.run(domain=body.get("domain", "business")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def visualization_handler(request: web.Request) -> web.Response:
    return json_response(executive_center.visualization.interactive_bundle())


async def enterprise_handler(request: web.Request) -> web.Response:
    try:
        ent = executive_center.enterprise
        if request.method == "GET":
            return json_response({
                "status": ent.status(),
                "audit": ent.audit_report(),
                "pack": ent.executive_report_pack(),
            })
        body = await _read_json(request)
        action = body.get("action", "company")
        if action == "organization":
            return json_response(ent.register_organization(company_id=body.get("company_id", ""), name=body.get("name", "")), status=201)
        if action == "region":
            return json_response(ent.register_region(company_id=body.get("company_id", ""), name=body.get("name", ""), code=body.get("code", "")), status=201)
        if action == "permission":
            return json_response(ent.grant_permission(principal=body.get("principal", ""), role=body.get("role", "viewer"), scope=body.get("scope", "global")), status=201)
        if action == "role_dashboard":
            return json_response(ent.role_based_dashboard(role=body.get("role", "viewer")))
        if action == "audit":
            return json_response(ent.audit(actor=body.get("actor", ""), action=body.get("audit_action", body.get("event", "")), resource=body.get("resource", "")), status=201)
        return json_response(ent.register_company(name=body.get("name", ""), region=body.get("region", "global")), status=201)
    except Exception as exc:
        return _handle_error(exc)
