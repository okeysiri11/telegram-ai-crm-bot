"""AI Runtime HTTP API — Sprint 36.3.

/api/ai-runtime/*
/api/llm/*
/api/prompts/*
/management/v1/ai-runtime/*
"""

from __future__ import annotations

from aiohttp import web

from platform_ai.service import ai_runtime_service as ars
from platform_management.permissions import ManagementRole, require_role


def _error(exc: Exception, *, status: int = 400) -> web.Response:
    return web.json_response(
        {"success": False, "error": str(exc), "errors": [str(exc)]},
        status=status,
    )


@require_role(ManagementRole.READ_ONLY)
async def status_handler(request: web.Request, ctx=None) -> web.Response:
    return web.json_response({"success": True, "data": ars.status()})


@require_role(ManagementRole.READ_ONLY)
async def providers_handler(request: web.Request, ctx=None) -> web.Response:
    data = await ars.providers()
    return web.json_response({"success": True, "data": {"providers": data, "count": len(data)}})


@require_role(ManagementRole.READ_ONLY)
async def models_handler(request: web.Request, ctx=None) -> web.Response:
    data = ars.models(provider_id=request.query.get("provider_id") or request.query.get("provider"))
    return web.json_response({"success": True, "data": {"models": data, "count": len(data)}})


@require_role(ManagementRole.READ_ONLY)
async def route_preview_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    try:
        data = ars.preview_route(body)
    except Exception as exc:
        return _error(exc, status=400)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def complete_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    try:
        data = await ars.complete(body)
    except Exception as exc:
        return _error(exc, status=400)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def llm_complete_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    try:
        data = await ars.complete(body)
    except Exception as exc:
        return _error(exc, status=400)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def sessions_create_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        body = await request.json()
    except Exception:
        body = {}
    data = ars.create_session(body if isinstance(body, dict) else {})
    return web.json_response({"success": True, "data": data}, status=201)


@require_role(ManagementRole.READ_ONLY)
async def sessions_list_handler(request: web.Request, ctx=None) -> web.Response:
    data = ars.list_sessions(status=request.query.get("status"))
    return web.json_response({"success": True, "data": {"sessions": data, "count": len(data)}})


@require_role(ManagementRole.READ_ONLY)
async def sessions_get_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        data = ars.get_session(request.match_info["id"])
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def sessions_close_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        data = ars.close_session(request.match_info["id"])
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def sessions_execute_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    body["session_id"] = request.match_info["id"]
    try:
        data = await ars.complete(body)
    except Exception as exc:
        return _error(exc, status=400)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.READ_ONLY)
async def prompts_list_handler(request: web.Request, ctx=None) -> web.Response:
    data = ars.list_prompts()
    return web.json_response({"success": True, "data": {"prompts": data, "count": len(data)}})


@require_role(ManagementRole.READ_ONLY)
async def prompts_get_handler(request: web.Request, ctx=None) -> web.Response:
    version = request.query.get("version")
    try:
        data = ars.get_prompt(request.match_info["id"], int(version) if version else None)
    except Exception as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def prompts_create_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = ars.create_prompt(body)
    return web.json_response({"success": True, "data": data}, status=201)


@require_role(ManagementRole.ADMINISTRATOR)
async def prompts_version_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    try:
        data = ars.version_prompt(request.match_info["id"], body)
    except Exception as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.READ_ONLY)
async def prompts_versions_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        data = ars.prompt_versions(request.match_info["id"])
    except Exception as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": {"versions": data}})


@require_role(ManagementRole.ADMINISTRATOR)
async def prompts_validate_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = ars.validate_prompt(request.match_info["id"], body)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def prompts_render_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    try:
        data = ars.render_prompt(request.match_info["id"], body)
    except Exception as exc:
        return _error(exc, status=400)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.READ_ONLY)
async def system_prompts_handler(request: web.Request, ctx=None) -> web.Response:
    return web.json_response({"success": True, "data": {"system_prompts": ars.system_prompts()}})


@require_role(ManagementRole.READ_ONLY)
async def tools_list_handler(request: web.Request, ctx=None) -> web.Response:
    data = ars.list_tools()
    return web.json_response({"success": True, "data": {"tools": data, "count": len(data)}})


@require_role(ManagementRole.ADMINISTRATOR)
async def tools_register_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = ars.register_tool(body)
    return web.json_response({"success": True, "data": data}, status=201)


@require_role(ManagementRole.READ_ONLY)
async def tools_schemas_handler(request: web.Request, ctx=None) -> web.Response:
    return web.json_response({"success": True, "data": {"functions": ars.function_schemas()}})


@require_role(ManagementRole.ADMINISTRATOR)
async def tools_execute_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    try:
        data = await ars.execute_tool(request.match_info["id"], body)
    except Exception as exc:
        return _error(exc, status=400)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.READ_ONLY)
async def tool_executions_handler(request: web.Request, ctx=None) -> web.Response:
    limit = int(request.query.get("limit") or 100)
    data = ars.tool_executions(limit=limit)
    return web.json_response({"success": True, "data": {"executions": data, "count": len(data)}})


@require_role(ManagementRole.READ_ONLY)
async def logs_handler(request: web.Request, ctx=None) -> web.Response:
    limit = int(request.query.get("limit") or 100)
    data = ars.logs(limit=limit)
    return web.json_response({"success": True, "data": {"logs": data, "count": len(data)}})


@require_role(ManagementRole.READ_ONLY)
async def monitoring_handler(request: web.Request, ctx=None) -> web.Response:
    return web.json_response({"success": True, "data": ars.monitoring()})


AI_RUNTIME_ROUTE_SPECS: list[tuple[str, str, object]] = [
    ("GET", "", status_handler),
    ("GET", "status", status_handler),
    ("GET", "providers", providers_handler),
    ("GET", "models", models_handler),
    ("POST", "route", route_preview_handler),
    ("POST", "complete", complete_handler),
    ("POST", "sessions", sessions_create_handler),
    ("GET", "sessions", sessions_list_handler),
    ("GET", "sessions/{id}", sessions_get_handler),
    ("POST", "sessions/{id}/close", sessions_close_handler),
    ("POST", "sessions/{id}/execute", sessions_execute_handler),
    ("GET", "prompts", prompts_list_handler),
    ("GET", "prompts/{id}", prompts_get_handler),
    ("POST", "prompts", prompts_create_handler),
    ("POST", "prompts/{id}/versions", prompts_version_handler),
    ("GET", "prompts/{id}/versions", prompts_versions_handler),
    ("POST", "prompts/{id}/validate", prompts_validate_handler),
    ("POST", "prompts/{id}/render", prompts_render_handler),
    ("GET", "system-prompts", system_prompts_handler),
    ("GET", "tools", tools_list_handler),
    ("POST", "tools", tools_register_handler),
    ("GET", "tools/functions", tools_schemas_handler),
    ("POST", "tools/{id}/execute", tools_execute_handler),
    ("GET", "tool-executions", tool_executions_handler),
    ("GET", "logs", logs_handler),
    ("GET", "monitoring", monitoring_handler),
]

LLM_ROUTE_SPECS: list[tuple[str, str, object]] = [
    ("POST", "complete", llm_complete_handler),
    ("POST", "chat", llm_complete_handler),
    ("GET", "providers", providers_handler),
    ("GET", "models", models_handler),
    ("POST", "route", route_preview_handler),
]

PROMPT_ROUTE_SPECS: list[tuple[str, str, object]] = [
    ("GET", "", prompts_list_handler),
    ("GET", "system", system_prompts_handler),
    ("GET", "{id}", prompts_get_handler),
    ("POST", "", prompts_create_handler),
    ("POST", "{id}/versions", prompts_version_handler),
    ("GET", "{id}/versions", prompts_versions_handler),
    ("POST", "{id}/validate", prompts_validate_handler),
    ("POST", "{id}/render", prompts_render_handler),
]


def _mount(app: web.Application, prefix: str, specs: list[tuple[str, str, object]]) -> None:
    for method, rel, handler in specs:
        rel = rel.strip("/")
        path = f"{prefix}/{rel}" if rel else prefix
        getattr(app.router, f"add_{method.lower()}")(path, handler)


def register_ai_runtime_routes(app: web.Application) -> None:
    from platform_api.versioning import MANAGEMENT_V1_PREFIX, register_dual_prefix_routes

    register_dual_prefix_routes(
        app,
        route_specs=AI_RUNTIME_ROUTE_SPECS,  # type: ignore[arg-type]
        v1_prefix=f"{MANAGEMENT_V1_PREFIX}/ai-runtime",
        legacy_prefix="/management/ai-runtime",
    )
    _mount(app, "/api/ai-runtime", AI_RUNTIME_ROUTE_SPECS)
    _mount(app, "/api/llm", LLM_ROUTE_SPECS)
    _mount(app, "/api/prompts", PROMPT_ROUTE_SPECS)
