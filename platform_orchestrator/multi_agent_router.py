"""Multi-Agent Runtime HTTP API — Sprint 36.7.

/api/agents/*
/api/multi-agent/*
/management/v1/agents/*
"""

from __future__ import annotations

from aiohttp import web

from platform_management.permissions import ManagementRole, require_role
from platform_orchestrator.multi_agent_service import multi_agent_runtime_service as mars


def _error(exc: Exception, *, status: int = 400) -> web.Response:
    return web.json_response(
        {"success": False, "error": str(exc), "errors": [str(exc)]},
        status=status,
    )


@require_role(ManagementRole.READ_ONLY)
async def status_handler(request: web.Request, ctx=None) -> web.Response:
    return web.json_response({"success": True, "data": mars.status()})


@require_role(ManagementRole.READ_ONLY)
async def agents_list_handler(request: web.Request, ctx=None) -> web.Response:
    available_only = request.query.get("available_only") == "1"
    data = mars.list_agents(available_only=available_only)
    return web.json_response({"success": True, "data": {"agents": data, "count": len(data)}})


@require_role(ManagementRole.ADMINISTRATOR)
async def agents_register_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = mars.register_agent(body)
    return web.json_response({"success": True, "data": data}, status=201)


@require_role(ManagementRole.READ_ONLY)
async def agents_get_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        data = mars.get_agent(request.match_info["id"])
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.READ_ONLY)
async def health_handler(request: web.Request, ctx=None) -> web.Response:
    data = mars.health()
    return web.json_response({"success": True, "data": {"health": data, "count": len(data)}})


@require_role(ManagementRole.ADMINISTRATOR)
async def sessions_create_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        body = await request.json()
    except Exception:
        body = {}
    data = mars.create_session(body if isinstance(body, dict) else {})
    return web.json_response({"success": True, "data": data}, status=201)


@require_role(ManagementRole.READ_ONLY)
async def sessions_list_handler(request: web.Request, ctx=None) -> web.Response:
    data = mars.list_sessions()
    return web.json_response({"success": True, "data": {"sessions": data, "count": len(data)}})


@require_role(ManagementRole.READ_ONLY)
async def sessions_get_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        data = mars.get_session(request.match_info["id"])
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def sessions_shared_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    try:
        data = mars.update_shared(request.match_info["id"], body)
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def messages_send_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = await mars.send_message(body)
    return web.json_response({"success": True, "data": data}, status=201)


@require_role(ManagementRole.ADMINISTRATOR)
async def messages_subscribe_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = mars.subscribe(body)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.READ_ONLY)
async def messages_list_handler(request: web.Request, ctx=None) -> web.Response:
    data = mars.list_messages()
    return web.json_response({"success": True, "data": {"messages": data, "count": len(data)}})


@require_role(ManagementRole.ADMINISTRATOR)
async def plan_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = mars.plan(body)
    return web.json_response({"success": True, "data": data}, status=201)


@require_role(ManagementRole.READ_ONLY)
async def plans_list_handler(request: web.Request, ctx=None) -> web.Response:
    data = mars.list_plans()
    return web.json_response({"success": True, "data": {"plans": data, "count": len(data)}})


@require_role(ManagementRole.READ_ONLY)
async def plans_get_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        data = mars.get_plan(request.match_info["id"])
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.READ_ONLY)
async def graph_handler(request: web.Request, ctx=None) -> web.Response:
    data = mars.task_graph(request.query.get("plan_id"))
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def tasks_create_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = mars.enqueue_task(body)
    return web.json_response({"success": True, "data": data}, status=201)


@require_role(ManagementRole.READ_ONLY)
async def tasks_list_handler(request: web.Request, ctx=None) -> web.Response:
    data = mars.list_tasks()
    return web.json_response({"success": True, "data": {"tasks": data, "count": len(data)}})


@require_role(ManagementRole.ADMINISTRATOR)
async def tasks_run_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        data = await mars.run_task(request.match_info["id"])
    except KeyError as exc:
        return _error(exc, status=404)
    except Exception as exc:
        return _error(exc, status=400)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def tasks_cancel_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        data = mars.cancel_task(request.match_info["id"])
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def tasks_checkpoint_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    try:
        data = mars.checkpoint_task(request.match_info["id"], body)
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def orchestrate_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    try:
        data = await mars.orchestrate(body)
    except Exception as exc:
        return _error(exc, status=400)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.READ_ONLY)
async def executions_handler(request: web.Request, ctx=None) -> web.Response:
    data = mars.list_executions()
    return web.json_response({"success": True, "data": {"executions": data, "count": len(data)}})


@require_role(ManagementRole.READ_ONLY)
async def statistics_handler(request: web.Request, ctx=None) -> web.Response:
    return web.json_response({"success": True, "data": mars.statistics()})


@require_role(ManagementRole.ADMINISTRATOR)
async def for_ai_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = await mars.for_ai_runtime(body)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def for_memory_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = await mars.for_project_memory(body)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def for_context_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = await mars.for_context_engine(body)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def for_workflow_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = await mars.for_workflow(body)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def for_sb_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = await mars.for_service_builder(body)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def for_voice_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = await mars.for_voice(body)
    return web.json_response({"success": True, "data": data})


MULTI_AGENT_ROUTE_SPECS: list[tuple[str, str, object]] = [
    ("GET", "", status_handler),
    ("GET", "status", status_handler),
    ("GET", "agents", agents_list_handler),
    ("POST", "agents", agents_register_handler),
    ("GET", "agents/{id}", agents_get_handler),
    ("GET", "health", health_handler),
    ("POST", "sessions", sessions_create_handler),
    ("GET", "sessions", sessions_list_handler),
    ("GET", "sessions/{id}", sessions_get_handler),
    ("POST", "sessions/{id}/shared", sessions_shared_handler),
    ("POST", "messages", messages_send_handler),
    ("POST", "messages/subscribe", messages_subscribe_handler),
    ("GET", "messages", messages_list_handler),
    ("POST", "plan", plan_handler),
    ("GET", "plans", plans_list_handler),
    ("GET", "plans/{id}", plans_get_handler),
    ("GET", "graph", graph_handler),
    ("POST", "tasks", tasks_create_handler),
    ("GET", "tasks", tasks_list_handler),
    ("POST", "tasks/{id}/run", tasks_run_handler),
    ("POST", "tasks/{id}/cancel", tasks_cancel_handler),
    ("POST", "tasks/{id}/checkpoint", tasks_checkpoint_handler),
    ("POST", "orchestrate", orchestrate_handler),
    ("GET", "executions", executions_handler),
    ("GET", "statistics", statistics_handler),
    ("POST", "integrations/ai-runtime", for_ai_handler),
    ("POST", "integrations/project-memory", for_memory_handler),
    ("POST", "integrations/context-engine", for_context_handler),
    ("POST", "integrations/workflow", for_workflow_handler),
    ("POST", "integrations/service-builder", for_sb_handler),
    ("POST", "integrations/voice", for_voice_handler),
]


def _mount(app: web.Application, prefix: str, specs: list[tuple[str, str, object]]) -> None:
    for method, rel, handler in specs:
        rel = rel.strip("/")
        path = f"{prefix}/{rel}" if rel else prefix
        getattr(app.router, f"add_{method.lower()}")(path, handler)


def register_multi_agent_runtime_routes(app: web.Application) -> None:
    from platform_api.versioning import MANAGEMENT_V1_PREFIX, register_dual_prefix_routes

    register_dual_prefix_routes(
        app,
        route_specs=MULTI_AGENT_ROUTE_SPECS,  # type: ignore[arg-type]
        v1_prefix=f"{MANAGEMENT_V1_PREFIX}/agents",
        legacy_prefix="/management/agents",
    )
    _mount(app, "/api/agents", MULTI_AGENT_ROUTE_SPECS)
    _mount(app, "/api/multi-agent", MULTI_AGENT_ROUTE_SPECS)
