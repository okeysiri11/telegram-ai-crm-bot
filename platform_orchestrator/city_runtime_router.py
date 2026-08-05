"""Enterprise City Runtime HTTP API — Sprint 37.0.

/api/platform/*
/api/dashboard/*
/api/search/*
/management/v1/platform/*
"""

from __future__ import annotations

from aiohttp import web

from platform_orchestrator.city_runtime_service import enterprise_city_runtime_service as crs
from platform_management.permissions import ManagementRole, require_role


def _error(exc: Exception, *, status: int = 400) -> web.Response:
    return web.json_response(
        {"success": False, "error": str(exc), "errors": [str(exc)]},
        status=status,
    )


@require_role(ManagementRole.READ_ONLY)
async def status_handler(request: web.Request, ctx=None) -> web.Response:
    return web.json_response({"success": True, "data": crs.status()})


@require_role(ManagementRole.READ_ONLY)
async def statistics_handler(request: web.Request, ctx=None) -> web.Response:
    return web.json_response({"success": True, "data": crs.statistics()})


@require_role(ManagementRole.READ_ONLY)
async def readiness_handler(request: web.Request, ctx=None) -> web.Response:
    return web.json_response({"success": True, "data": crs.production_readiness()})


@require_role(ManagementRole.READ_ONLY)
async def services_list_handler(request: web.Request, ctx=None) -> web.Response:
    data = crs.list_services(category=request.query.get("category"))
    return web.json_response({"success": True, "data": {"services": data, "count": len(data)}})


@require_role(ManagementRole.ADMINISTRATOR)
async def services_register_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = crs.register_service(body)
    return web.json_response({"success": True, "data": data}, status=201)


@require_role(ManagementRole.READ_ONLY)
async def service_get_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        data = crs.get_service(request.match_info["id"])
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.READ_ONLY)
async def navigation_handler(request: web.Request, ctx=None) -> web.Response:
    data = crs.navigation()
    return web.json_response({"success": True, "data": {"navigation": data, "count": len(data)}})


@require_role(ManagementRole.READ_ONLY)
async def workspace_handler(request: web.Request, ctx=None) -> web.Response:
    data = crs.workspace()
    return web.json_response({"success": True, "data": {"modules": data, "count": len(data)}})


@require_role(ManagementRole.READ_ONLY)
async def palette_handler(request: web.Request, ctx=None) -> web.Response:
    data = crs.command_palette(request.query.get("q") or request.query.get("query") or "")
    return web.json_response({"success": True, "data": {"commands": data, "count": len(data)}})


@require_role(ManagementRole.ADMINISTRATOR)
async def route_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = crs.route_to(str(body.get("target") or body.get("route") or ""), session_id=body.get("session_id"))
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def sessions_create_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        body = await request.json()
    except Exception:
        body = {}
    data = crs.create_session(body if isinstance(body, dict) else {})
    return web.json_response({"success": True, "data": data}, status=201)


@require_role(ManagementRole.READ_ONLY)
async def sessions_list_handler(request: web.Request, ctx=None) -> web.Response:
    data = crs.list_sessions()
    return web.json_response({"success": True, "data": {"sessions": data, "count": len(data)}})


@require_role(ManagementRole.READ_ONLY)
async def session_get_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        data = crs.get_session(request.match_info["id"])
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def session_shared_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    try:
        data = crs.update_shared(request.match_info["id"], body)
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def events_publish_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = crs.publish_event(body)
    return web.json_response({"success": True, "data": data}, status=201)


@require_role(ManagementRole.READ_ONLY)
async def events_list_handler(request: web.Request, ctx=None) -> web.Response:
    limit = int(request.query.get("limit") or 100)
    data = crs.list_events(limit=limit)
    return web.json_response({"success": True, "data": {"events": data, "count": len(data)}})


@require_role(ManagementRole.ADMINISTRATOR)
async def notify_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = crs.notify(body)
    return web.json_response({"success": True, "data": data}, status=201)


@require_role(ManagementRole.READ_ONLY)
async def notifications_handler(request: web.Request, ctx=None) -> web.Response:
    unread = (request.query.get("unread") or "").lower() in ("1", "true", "yes")
    data = crs.list_notifications(unread_only=unread)
    return web.json_response({"success": True, "data": {"notifications": data, "count": len(data)}})


@require_role(ManagementRole.ADMINISTRATOR)
async def notification_read_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        data = crs.mark_read(request.match_info["id"])
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.READ_ONLY)
async def health_list_handler(request: web.Request, ctx=None) -> web.Response:
    data = crs.list_health()
    return web.json_response(
        {
            "success": True,
            "data": {"components": data, "count": len(data), "overall": crs.engine.overall_health()},
        }
    )


@require_role(ManagementRole.ADMINISTRATOR)
async def health_set_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = crs.set_health(request.match_info["id"], body)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.READ_ONLY)
async def metrics_handler(request: web.Request, ctx=None) -> web.Response:
    data = crs.list_metrics()
    return web.json_response({"success": True, "data": {"metrics": data, "count": len(data)}})


@require_role(ManagementRole.ADMINISTRATOR)
async def metrics_upsert_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = crs.upsert_metric(body)
    return web.json_response({"success": True, "data": data}, status=201)


@require_role(ManagementRole.READ_ONLY)
async def config_list_handler(request: web.Request, ctx=None) -> web.Response:
    data = crs.list_config()
    return web.json_response({"success": True, "data": {"config": data, "count": len(data)}})


@require_role(ManagementRole.ADMINISTRATOR)
async def config_set_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = crs.set_config(body)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.READ_ONLY)
async def usage_handler(request: web.Request, ctx=None) -> web.Response:
    data = crs.list_usage(limit=int(request.query.get("limit") or 100))
    return web.json_response({"success": True, "data": {"usage": data, "count": len(data)}})


@require_role(ManagementRole.READ_ONLY)
async def activity_handler(request: web.Request, ctx=None) -> web.Response:
    data = crs.list_activity(limit=int(request.query.get("limit") or 100))
    return web.json_response({"success": True, "data": {"activity": data, "count": len(data)}})


@require_role(ManagementRole.ADMINISTRATOR)
async def command_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = await crs.execute_command(body)
    return web.json_response({"success": True, "data": data}, status=201)


@require_role(ManagementRole.READ_ONLY)
async def commands_list_handler(request: web.Request, ctx=None) -> web.Response:
    data = crs.list_commands(limit=int(request.query.get("limit") or 50))
    return web.json_response({"success": True, "data": {"commands": data, "count": len(data)}})


@require_role(ManagementRole.ADMINISTRATOR)
async def integrations_probe_handler(request: web.Request, ctx=None) -> web.Response:
    data = await crs.probe_integrations()
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.READ_ONLY)
async def dashboard_handler(request: web.Request, ctx=None) -> web.Response:
    return web.json_response({"success": True, "data": crs.dashboard()})


@require_role(ManagementRole.READ_ONLY)
async def search_handler(request: web.Request, ctx=None) -> web.Response:
    q = request.query.get("q") or request.query.get("query") or ""
    kind = request.query.get("kind")
    limit = int(request.query.get("limit") or 20)
    data = crs.search(q, kind=kind, limit=limit)
    return web.json_response({"success": True, "data": {"hits": data, "count": len(data), "query": q}})


@require_role(ManagementRole.ADMINISTRATOR)
async def search_post_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = crs.search(
        str(body.get("query") or body.get("q") or ""),
        kind=body.get("kind"),
        limit=int(body.get("limit") or 20),
    )
    return web.json_response({"success": True, "data": {"hits": data, "count": len(data)}})


# Integration endpoints
@require_role(ManagementRole.ADMINISTRATOR)
async def for_ai_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    return web.json_response({"success": True, "data": await crs.for_ai_runtime(body)})


@require_role(ManagementRole.ADMINISTRATOR)
async def for_multi_agent_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    return web.json_response({"success": True, "data": await crs.for_multi_agent(body)})


@require_role(ManagementRole.ADMINISTRATOR)
async def for_memory_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    return web.json_response({"success": True, "data": await crs.for_project_memory(body)})


@require_role(ManagementRole.ADMINISTRATOR)
async def for_context_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    return web.json_response({"success": True, "data": await crs.for_context_engine(body)})


@require_role(ManagementRole.ADMINISTRATOR)
async def for_creative_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    return web.json_response({"success": True, "data": await crs.for_creative(body)})


@require_role(ManagementRole.ADMINISTRATOR)
async def for_voice_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    return web.json_response({"success": True, "data": await crs.for_voice(body)})


@require_role(ManagementRole.ADMINISTRATOR)
async def for_skills_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    return web.json_response({"success": True, "data": await crs.for_skills(body)})


@require_role(ManagementRole.ADMINISTRATOR)
async def for_workflow_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    return web.json_response({"success": True, "data": await crs.for_workflow(body)})


@require_role(ManagementRole.ADMINISTRATOR)
async def for_event_bus_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    return web.json_response({"success": True, "data": await crs.for_event_bus(body)})


PLATFORM_ROUTE_SPECS: list[tuple[str, str, object]] = [
    ("GET", "", status_handler),
    ("GET", "status", status_handler),
    ("GET", "statistics", statistics_handler),
    ("GET", "readiness", readiness_handler),
    ("GET", "services", services_list_handler),
    ("POST", "services", services_register_handler),
    ("GET", "services/{id}", service_get_handler),
    ("GET", "navigation", navigation_handler),
    ("GET", "workspace", workspace_handler),
    ("GET", "palette", palette_handler),
    ("POST", "route", route_handler),
    ("GET", "sessions", sessions_list_handler),
    ("POST", "sessions", sessions_create_handler),
    ("GET", "sessions/{id}", session_get_handler),
    ("POST", "sessions/{id}/shared", session_shared_handler),
    ("GET", "events", events_list_handler),
    ("POST", "events", events_publish_handler),
    ("GET", "notifications", notifications_handler),
    ("POST", "notifications", notify_handler),
    ("POST", "notifications/{id}/read", notification_read_handler),
    ("GET", "health", health_list_handler),
    ("POST", "health/{id}", health_set_handler),
    ("GET", "metrics", metrics_handler),
    ("POST", "metrics", metrics_upsert_handler),
    ("GET", "config", config_list_handler),
    ("POST", "config", config_set_handler),
    ("GET", "usage", usage_handler),
    ("GET", "activity", activity_handler),
    ("POST", "command", command_handler),
    ("GET", "commands", commands_list_handler),
    ("POST", "integrations/probe", integrations_probe_handler),
    ("POST", "integrations/ai-runtime", for_ai_handler),
    ("POST", "integrations/multi-agent", for_multi_agent_handler),
    ("POST", "integrations/project-memory", for_memory_handler),
    ("POST", "integrations/context-engine", for_context_handler),
    ("POST", "integrations/creative", for_creative_handler),
    ("POST", "integrations/voice", for_voice_handler),
    ("POST", "integrations/skills-sdk", for_skills_handler),
    ("POST", "integrations/workflow", for_workflow_handler),
    ("POST", "integrations/event-bus", for_event_bus_handler),
]

DASHBOARD_ROUTE_SPECS: list[tuple[str, str, object]] = [
    ("GET", "", dashboard_handler),
    ("GET", "overview", dashboard_handler),
    ("GET", "kpis", dashboard_handler),
]

SEARCH_ROUTE_SPECS: list[tuple[str, str, object]] = [
    ("GET", "", search_handler),
    ("GET", "query", search_handler),
    ("POST", "", search_post_handler),
    ("POST", "query", search_post_handler),
]


def _mount(app: web.Application, prefix: str, specs: list[tuple[str, str, object]]) -> None:
    for method, rel, handler in specs:
        rel = rel.strip("/")
        path = f"{prefix}/{rel}" if rel else prefix
        add = getattr(app.router, f"add_{method.lower()}")
        add(path, handler)
        if not rel:
            add(f"{prefix}/", handler)


def register_enterprise_city_runtime_routes(app: web.Application) -> None:
    from platform_api.versioning import MANAGEMENT_V1_PREFIX, register_dual_prefix_routes

    register_dual_prefix_routes(
        app,
        route_specs=PLATFORM_ROUTE_SPECS,  # type: ignore[arg-type]
        v1_prefix=f"{MANAGEMENT_V1_PREFIX}/platform",
        legacy_prefix="/management/enterprise-city",
    )
    _mount(app, "/api/platform", PLATFORM_ROUTE_SPECS)
    _mount(app, "/api/dashboard", DASHBOARD_ROUTE_SPECS)
    _mount(app, "/api/search", SEARCH_ROUTE_SPECS)
    # Honor svc seed aliases
    _mount(app, "/api/city", PLATFORM_ROUTE_SPECS)
    _mount(app, "/city", [("GET", "simulate", status_handler), ("GET", "", status_handler)])
