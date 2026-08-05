"""Project Memory Engine HTTP API — Sprint 36.5.

/api/project-memory/*
/api/memory/*
/management/v1/project-memory/*
"""

from __future__ import annotations

from aiohttp import web

from platform_management.permissions import ManagementRole, require_role
from platform_memory.project_memory_service import project_memory_service as pms


def _error(exc: Exception, *, status: int = 400) -> web.Response:
    return web.json_response(
        {"success": False, "error": str(exc), "errors": [str(exc)]},
        status=status,
    )


@require_role(ManagementRole.READ_ONLY)
async def status_handler(request: web.Request, ctx=None) -> web.Response:
    return web.json_response({"success": True, "data": pms.status()})


@require_role(ManagementRole.ADMINISTRATOR)
async def remember_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    try:
        data = await pms.remember(body)
    except Exception as exc:
        return _error(exc, status=400)
    return web.json_response({"success": True, "data": data}, status=201)


@require_role(ManagementRole.READ_ONLY)
async def list_handler(request: web.Request, ctx=None) -> web.Response:
    data = pms.list_memories(
        kind=request.query.get("kind"),
        layer=request.query.get("layer"),
        project_id=request.query.get("project_id"),
        agent_id=request.query.get("agent_id"),
    )
    return web.json_response({"success": True, "data": {"memories": data, "count": len(data)}})


@require_role(ManagementRole.READ_ONLY)
async def get_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        data = pms.get(request.match_info["id"])
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def forget_handler(request: web.Request, ctx=None) -> web.Response:
    return web.json_response({"success": True, "data": pms.forget(request.match_info["id"])})


@require_role(ManagementRole.READ_ONLY)
async def chunks_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        data = pms.chunks(request.match_info["id"])
    except Exception as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": {"chunks": data, "count": len(data)}})


@require_role(ManagementRole.ADMINISTRATOR)
async def search_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        body = await request.json()
    except Exception:
        body = {
            "query": request.query.get("query") or "",
            "kind": request.query.get("kind"),
            "layer": request.query.get("layer"),
            "project_id": request.query.get("project_id"),
        }
    data = await pms.search(body if isinstance(body, dict) else {})
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def link_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    try:
        data = pms.link(body)
    except Exception as exc:
        return _error(exc, status=400)
    return web.json_response({"success": True, "data": data}, status=201)


@require_role(ManagementRole.READ_ONLY)
async def graph_handler(request: web.Request, ctx=None) -> web.Response:
    data = pms.graph(project_id=request.query.get("project_id"))
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def sessions_create_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        body = await request.json()
    except Exception:
        body = {}
    data = pms.create_session(body if isinstance(body, dict) else {})
    return web.json_response({"success": True, "data": data}, status=201)


@require_role(ManagementRole.READ_ONLY)
async def sessions_list_handler(request: web.Request, ctx=None) -> web.Response:
    data = pms.list_sessions()
    return web.json_response({"success": True, "data": {"sessions": data, "count": len(data)}})


@require_role(ManagementRole.READ_ONLY)
async def sessions_get_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        data = pms.get_session(request.match_info["id"])
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def sessions_pin_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    try:
        data = pms.pin(request.match_info["id"], str(body.get("memory_id") or ""))
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.READ_ONLY)
async def timeline_handler(request: web.Request, ctx=None) -> web.Response:
    limit = int(request.query.get("limit") or 100)
    data = pms.timeline(limit=limit)
    return web.json_response({"success": True, "data": {"timeline": data, "count": len(data)}})


@require_role(ManagementRole.ADMINISTRATOR)
async def feedback_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    try:
        data = pms.feedback(body)
    except KeyError as exc:
        return _error(exc, status=404)
    except Exception as exc:
        return _error(exc, status=400)
    return web.json_response({"success": True, "data": data}, status=201)


@require_role(ManagementRole.READ_ONLY)
async def analytics_handler(request: web.Request, ctx=None) -> web.Response:
    return web.json_response({"success": True, "data": pms.analytics()})


@require_role(ManagementRole.ADMINISTRATOR)
async def agent_write_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    agent_id = request.match_info["agent_id"]
    payload = {**body, "kind": body.get("kind") or "agent", "agent_id": agent_id}
    data = await pms.remember(payload)
    return web.json_response({"success": True, "data": data}, status=201)


@require_role(ManagementRole.READ_ONLY)
async def agent_read_handler(request: web.Request, ctx=None) -> web.Response:
    agent_id = request.match_info["agent_id"]
    data = pms.list_memories(agent_id=agent_id, kind=request.query.get("kind") or "agent")
    return web.json_response({"success": True, "data": {"memories": data, "count": len(data)}})


@require_role(ManagementRole.ADMINISTRATOR)
async def for_ai_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = await pms.for_ai_runtime(body)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def for_context_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = await pms.for_context_engine(body)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def for_workflow_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = await pms.for_workflow(body)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def for_service_builder_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = await pms.for_service_builder(body)
    return web.json_response({"success": True, "data": data})


PROJECT_MEMORY_ROUTE_SPECS: list[tuple[str, str, object]] = [
    ("GET", "", status_handler),
    ("GET", "status", status_handler),
    ("POST", "remember", remember_handler),
    ("GET", "memories", list_handler),
    ("GET", "memories/{id}", get_handler),
    ("DELETE", "memories/{id}", forget_handler),
    ("GET", "memories/{id}/chunks", chunks_handler),
    ("POST", "search", search_handler),
    ("GET", "search", search_handler),
    ("POST", "relations", link_handler),
    ("GET", "graph", graph_handler),
    ("POST", "sessions", sessions_create_handler),
    ("GET", "sessions", sessions_list_handler),
    ("GET", "sessions/{id}", sessions_get_handler),
    ("POST", "sessions/{id}/pin", sessions_pin_handler),
    ("GET", "timeline", timeline_handler),
    ("POST", "feedback", feedback_handler),
    ("GET", "analytics", analytics_handler),
    ("POST", "agents/{agent_id}/remember", agent_write_handler),
    ("GET", "agents/{agent_id}/memories", agent_read_handler),
    ("POST", "integrations/ai-runtime", for_ai_handler),
    ("POST", "integrations/context-engine", for_context_handler),
    ("POST", "integrations/workflow", for_workflow_handler),
    ("POST", "integrations/service-builder", for_service_builder_handler),
]


def _mount(app: web.Application, prefix: str, specs: list[tuple[str, str, object]]) -> None:
    for method, rel, handler in specs:
        rel = rel.strip("/")
        path = f"{prefix}/{rel}" if rel else prefix
        getattr(app.router, f"add_{method.lower()}")(path, handler)


def register_project_memory_routes(app: web.Application) -> None:
    from platform_api.versioning import MANAGEMENT_V1_PREFIX, register_dual_prefix_routes

    register_dual_prefix_routes(
        app,
        route_specs=PROJECT_MEMORY_ROUTE_SPECS,  # type: ignore[arg-type]
        v1_prefix=f"{MANAGEMENT_V1_PREFIX}/project-memory",
        legacy_prefix="/management/project-memory",
    )
    _mount(app, "/api/project-memory", PROJECT_MEMORY_ROUTE_SPECS)
    _mount(app, "/api/memory", PROJECT_MEMORY_ROUTE_SPECS)
