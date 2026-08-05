"""AI Skills & SDK HTTP API — Sprint 36.8.

/api/skills/*
/api/sdk/*
/management/v1/skills/*
"""

from __future__ import annotations

from aiohttp import web

from platform_ai.skills_sdk_service import skills_sdk_service as sss
from platform_management.permissions import ManagementRole, require_role


def _error(exc: Exception, *, status: int = 400) -> web.Response:
    return web.json_response(
        {"success": False, "error": str(exc), "errors": [str(exc)]},
        status=status,
    )


@require_role(ManagementRole.READ_ONLY)
async def status_handler(request: web.Request, ctx=None) -> web.Response:
    return web.json_response({"success": True, "data": sss.status()})


@require_role(ManagementRole.READ_ONLY)
async def list_handler(request: web.Request, ctx=None) -> web.Response:
    data = sss.list_skills(
        category=request.query.get("category"),
        visibility=request.query.get("visibility"),
    )
    return web.json_response({"success": True, "data": {"skills": data, "count": len(data)}})


@require_role(ManagementRole.ADMINISTRATOR)
async def register_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = sss.register(body)
    return web.json_response({"success": True, "data": data}, status=201)


@require_role(ManagementRole.READ_ONLY)
async def get_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        data = sss.get_skill(request.match_info["id"])
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.READ_ONLY)
async def versions_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        data = sss.list_versions(request.match_info["id"])
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": {"versions": data, "count": len(data)}})


@require_role(ManagementRole.ADMINISTRATOR)
async def publish_version_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    try:
        data = sss.publish_version(request.match_info["id"], body)
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data}, status=201)


@require_role(ManagementRole.ADMINISTRATOR)
async def install_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        body = await request.json()
    except Exception:
        body = {}
    try:
        data = sss.install(request.match_info["id"], body if isinstance(body, dict) else {})
    except Exception as exc:
        return _error(exc, status=400)
    return web.json_response({"success": True, "data": data}, status=201)


@require_role(ManagementRole.ADMINISTRATOR)
async def uninstall_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        data = sss.uninstall(request.match_info["id"])
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def enable_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        data = sss.enable(request.match_info["id"])
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def disable_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        data = sss.disable(request.match_info["id"])
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.READ_ONLY)
async def installed_handler(request: web.Request, ctx=None) -> web.Response:
    data = sss.list_installed()
    return web.json_response({"success": True, "data": {"installed": data, "count": len(data)}})


@require_role(ManagementRole.ADMINISTRATOR)
async def execute_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = await sss.execute(body)
    status = 200 if data.get("success") else 400
    return web.json_response({"success": True, "data": data}, status=status if data.get("success") else 200)


@require_role(ManagementRole.READ_ONLY)
async def marketplace_handler(request: web.Request, ctx=None) -> web.Response:
    data = sss.marketplace(repository=request.query.get("repository"))
    return web.json_response({"success": True, "data": {"listings": data, "count": len(data)}})


@require_role(ManagementRole.ADMINISTRATOR)
async def rate_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    try:
        data = sss.rate(request.match_info["id"], body)
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.READ_ONLY)
async def updates_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        data = sss.updates(request.match_info["id"])
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.READ_ONLY)
async def statistics_handler(request: web.Request, ctx=None) -> web.Response:
    return web.json_response({"success": True, "data": sss.statistics()})


@require_role(ManagementRole.READ_ONLY)
async def executions_handler(request: web.Request, ctx=None) -> web.Response:
    data = sss.list_executions()
    return web.json_response({"success": True, "data": {"executions": data, "count": len(data)}})


@require_role(ManagementRole.READ_ONLY)
async def sdk_manifest_handler(request: web.Request, ctx=None) -> web.Response:
    return web.json_response({"success": True, "data": sss.sdk_manifest()})


@require_role(ManagementRole.READ_ONLY)
async def templates_handler(request: web.Request, ctx=None) -> web.Response:
    data = sss.templates(kind=request.query.get("kind"))
    return web.json_response({"success": True, "data": {"templates": data, "count": len(data)}})


@require_role(ManagementRole.READ_ONLY)
async def template_get_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        data = sss.get_template(request.match_info["id"])
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def for_ai_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = await sss.for_ai_runtime(body)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def for_multi_agent_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = await sss.for_multi_agent(body)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def for_memory_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = await sss.for_project_memory(body)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def for_context_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = await sss.for_context_engine(body)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def for_workflow_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = await sss.for_workflow(body)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def for_voice_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = await sss.for_voice(body)
    return web.json_response({"success": True, "data": data})


SKILLS_ROUTE_SPECS: list[tuple[str, str, object]] = [
    ("GET", "", status_handler),
    ("GET", "status", status_handler),
    ("GET", "skills", list_handler),
    ("POST", "skills", register_handler),
    ("GET", "skills/{id}", get_handler),
    ("GET", "skills/{id}/versions", versions_handler),
    ("POST", "skills/{id}/versions", publish_version_handler),
    ("POST", "skills/{id}/install", install_handler),
    ("POST", "skills/{id}/uninstall", uninstall_handler),
    ("POST", "skills/{id}/enable", enable_handler),
    ("POST", "skills/{id}/disable", disable_handler),
    ("GET", "skills/{id}/updates", updates_handler),
    ("POST", "skills/{id}/rate", rate_handler),
    ("GET", "installed", installed_handler),
    ("POST", "execute", execute_handler),
    ("GET", "marketplace", marketplace_handler),
    ("GET", "statistics", statistics_handler),
    ("GET", "executions", executions_handler),
    ("POST", "integrations/ai-runtime", for_ai_handler),
    ("POST", "integrations/multi-agent", for_multi_agent_handler),
    ("POST", "integrations/project-memory", for_memory_handler),
    ("POST", "integrations/context-engine", for_context_handler),
    ("POST", "integrations/workflow", for_workflow_handler),
    ("POST", "integrations/voice", for_voice_handler),
]

SDK_ROUTE_SPECS: list[tuple[str, str, object]] = [
    ("GET", "", sdk_manifest_handler),
    ("GET", "manifest", sdk_manifest_handler),
    ("GET", "templates", templates_handler),
    ("GET", "templates/{id}", template_get_handler),
]


def _mount(app: web.Application, prefix: str, specs: list[tuple[str, str, object]]) -> None:
    for method, rel, handler in specs:
        rel = rel.strip("/")
        path = f"{prefix}/{rel}" if rel else prefix
        getattr(app.router, f"add_{method.lower()}")(path, handler)


def register_skills_sdk_routes(app: web.Application) -> None:
    from platform_api.versioning import MANAGEMENT_V1_PREFIX, register_dual_prefix_routes

    register_dual_prefix_routes(
        app,
        route_specs=SKILLS_ROUTE_SPECS,  # type: ignore[arg-type]
        v1_prefix=f"{MANAGEMENT_V1_PREFIX}/skills",
        legacy_prefix="/management/skills-sdk",
    )
    _mount(app, "/api/skills", SKILLS_ROUTE_SPECS)
    _mount(app, "/api/sdk", SDK_ROUTE_SPECS)
