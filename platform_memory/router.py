"""Context Engine HTTP API — Sprint 36.4.

/api/context/*
/api/context-engine/*
/management/v1/context/*
"""

from __future__ import annotations

from aiohttp import web

from platform_management.permissions import ManagementRole, require_role
from platform_memory.service import context_engine_service as ces


def _error(exc: Exception, *, status: int = 400) -> web.Response:
    return web.json_response(
        {"success": False, "error": str(exc), "errors": [str(exc)]},
        status=status,
    )


@require_role(ManagementRole.READ_ONLY)
async def status_handler(request: web.Request, ctx=None) -> web.Response:
    return web.json_response({"success": True, "data": ces.status()})


@require_role(ManagementRole.ADMINISTRATOR)
async def resolve_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    try:
        data = await ces.resolve(body)
    except Exception as exc:
        return _error(exc, status=400)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.READ_ONLY)
async def sources_handler(request: web.Request, ctx=None) -> web.Response:
    data = ces.list_sources()
    return web.json_response({"success": True, "data": {"sources": data, "count": len(data)}})


@require_role(ManagementRole.READ_ONLY)
async def graph_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        body = await request.json()
    except Exception:
        body = {}
    if request.method == "GET":
        body = {
            "query": request.query.get("query"),
            "principal": request.query.get("principal"),
        }
    data = ces.graph(body if isinstance(body, dict) else {})
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def sessions_create_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        body = await request.json()
    except Exception:
        body = {}
    data = ces.create_session(body if isinstance(body, dict) else {})
    return web.json_response({"success": True, "data": data}, status=201)


@require_role(ManagementRole.READ_ONLY)
async def sessions_list_handler(request: web.Request, ctx=None) -> web.Response:
    data = ces.list_sessions()
    return web.json_response({"success": True, "data": {"sessions": data, "count": len(data)}})


@require_role(ManagementRole.READ_ONLY)
async def sessions_get_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        data = ces.get_session(request.match_info["id"])
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.READ_ONLY)
async def cache_list_handler(request: web.Request, ctx=None) -> web.Response:
    data = ces.cache_entries()
    return web.json_response(
        {"success": True, "data": {"entries": data, "stats": ces.cache_stats(), "count": len(data)}}
    )


@require_role(ManagementRole.ADMINISTRATOR)
async def cache_clear_handler(request: web.Request, ctx=None) -> web.Response:
    return web.json_response({"success": True, "data": ces.clear_cache()})


@require_role(ManagementRole.READ_ONLY)
async def history_handler(request: web.Request, ctx=None) -> web.Response:
    limit = int(request.query.get("limit") or 100)
    data = ces.history(limit=limit)
    return web.json_response({"success": True, "data": {"history": data, "count": len(data)}})


@require_role(ManagementRole.READ_ONLY)
async def permissions_list_handler(request: web.Request, ctx=None) -> web.Response:
    data = ces.permissions()
    return web.json_response({"success": True, "data": {"permissions": data, "count": len(data)}})


@require_role(ManagementRole.ADMINISTRATOR)
async def permissions_grant_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = ces.grant_permission(body)
    return web.json_response({"success": True, "data": data}, status=201)


@require_role(ManagementRole.READ_ONLY)
async def statistics_handler(request: web.Request, ctx=None) -> web.Response:
    return web.json_response({"success": True, "data": ces.statistics()})


@require_role(ManagementRole.READ_ONLY)
async def embeddings_handler(request: web.Request, ctx=None) -> web.Response:
    limit = int(request.query.get("limit") or 50)
    data = ces.embeddings(limit=limit)
    return web.json_response({"success": True, "data": {"embeddings": data, "count": len(data)}})


@require_role(ManagementRole.ADMINISTRATOR)
async def for_ai_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = await ces.for_ai_runtime(body)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def for_workflow_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = await ces.for_workflow(body)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def for_service_builder_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = await ces.for_service_builder(body)
    return web.json_response({"success": True, "data": data})


CONTEXT_ROUTE_SPECS: list[tuple[str, str, object]] = [
    ("GET", "", status_handler),
    ("GET", "status", status_handler),
    ("POST", "resolve", resolve_handler),
    ("GET", "sources", sources_handler),
    ("GET", "graph", graph_handler),
    ("POST", "graph", graph_handler),
    ("POST", "sessions", sessions_create_handler),
    ("GET", "sessions", sessions_list_handler),
    ("GET", "sessions/{id}", sessions_get_handler),
    ("GET", "cache", cache_list_handler),
    ("POST", "cache/clear", cache_clear_handler),
    ("GET", "history", history_handler),
    ("GET", "permissions", permissions_list_handler),
    ("POST", "permissions", permissions_grant_handler),
    ("GET", "statistics", statistics_handler),
    ("GET", "embeddings", embeddings_handler),
    ("POST", "integrations/ai-runtime", for_ai_handler),
    ("POST", "integrations/workflow", for_workflow_handler),
    ("POST", "integrations/service-builder", for_service_builder_handler),
]


def _mount(app: web.Application, prefix: str, specs: list[tuple[str, str, object]]) -> None:
    for method, rel, handler in specs:
        rel = rel.strip("/")
        path = f"{prefix}/{rel}" if rel else prefix
        getattr(app.router, f"add_{method.lower()}")(path, handler)


def register_context_engine_routes(app: web.Application) -> None:
    from platform_api.versioning import MANAGEMENT_V1_PREFIX, register_dual_prefix_routes

    register_dual_prefix_routes(
        app,
        route_specs=CONTEXT_ROUTE_SPECS,  # type: ignore[arg-type]
        v1_prefix=f"{MANAGEMENT_V1_PREFIX}/context",
        legacy_prefix="/management/context",
    )
    _mount(app, "/api/context", CONTEXT_ROUTE_SPECS)
    _mount(app, "/api/context-engine", CONTEXT_ROUTE_SPECS)
