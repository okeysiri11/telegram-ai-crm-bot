"""Voice Command Center HTTP API — Sprint 36.6.

/api/voice/*
/api/voice-runtime/*
/management/v1/voice/*
"""

from __future__ import annotations

from aiohttp import web

from platform_ai.voice_service import voice_runtime_service as vrs
from platform_management.permissions import ManagementRole, require_role


def _error(exc: Exception, *, status: int = 400) -> web.Response:
    return web.json_response(
        {"success": False, "error": str(exc), "errors": [str(exc)]},
        status=status,
    )


@require_role(ManagementRole.READ_ONLY)
async def status_handler(request: web.Request, ctx=None) -> web.Response:
    return web.json_response({"success": True, "data": vrs.status()})


@require_role(ManagementRole.READ_ONLY)
async def providers_handler(request: web.Request, ctx=None) -> web.Response:
    data = await vrs.providers()
    return web.json_response({"success": True, "data": {"providers": data, "count": len(data)}})


@require_role(ManagementRole.ADMINISTRATOR)
async def sessions_create_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        body = await request.json()
    except Exception:
        body = {}
    data = vrs.start_session(body if isinstance(body, dict) else {})
    return web.json_response({"success": True, "data": data}, status=201)


@require_role(ManagementRole.READ_ONLY)
async def sessions_list_handler(request: web.Request, ctx=None) -> web.Response:
    data = vrs.list_sessions()
    return web.json_response({"success": True, "data": {"sessions": data, "count": len(data)}})


@require_role(ManagementRole.READ_ONLY)
async def sessions_get_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        data = vrs.get_session(request.match_info["id"])
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def sessions_stop_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        data = vrs.stop_session(request.match_info["id"])
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def sessions_mode_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    try:
        data = vrs.set_mode(request.match_info["id"], str(body.get("mode") or "push_to_talk"))
    except Exception as exc:
        return _error(exc, status=400)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def vad_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    try:
        data = vrs.vad(request.match_info["id"], energy=float(body.get("energy") or 0.5))
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def wake_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    try:
        data = vrs.wake_word(request.match_info["id"], str(body.get("text") or ""))
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def process_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    try:
        data = await vrs.process(body)
    except Exception as exc:
        return _error(exc, status=400)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def confirm_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    command_id = request.match_info.get("id") or body.get("command_id")
    try:
        data = await vrs.confirm(str(command_id), approved_by=str(body.get("approved_by") or "admin"))
    except KeyError as exc:
        return _error(exc, status=404)
    except Exception as exc:
        return _error(exc, status=400)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def parse_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = vrs.parse(str(body.get("transcript") or body.get("text") or ""))
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.READ_ONLY)
async def commands_handler(request: web.Request, ctx=None) -> web.Response:
    limit = int(request.query.get("limit") or 100)
    data = vrs.list_commands(limit=limit)
    return web.json_response({"success": True, "data": {"commands": data, "count": len(data)}})


@require_role(ManagementRole.READ_ONLY)
async def history_handler(request: web.Request, ctx=None) -> web.Response:
    limit = int(request.query.get("limit") or 100)
    data = vrs.history(limit=limit)
    return web.json_response({"success": True, "data": {"history": data, "count": len(data)}})


@require_role(ManagementRole.READ_ONLY)
async def devices_list_handler(request: web.Request, ctx=None) -> web.Response:
    data = vrs.list_devices()
    return web.json_response({"success": True, "data": {"devices": data, "count": len(data)}})


@require_role(ManagementRole.ADMINISTRATOR)
async def devices_create_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = vrs.register_device(body)
    return web.json_response({"success": True, "data": data}, status=201)


@require_role(ManagementRole.READ_ONLY)
async def profiles_list_handler(request: web.Request, ctx=None) -> web.Response:
    data = vrs.list_profiles()
    return web.json_response({"success": True, "data": {"profiles": data, "count": len(data)}})


@require_role(ManagementRole.ADMINISTRATOR)
async def profiles_upsert_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = vrs.upsert_profile(body)
    return web.json_response({"success": True, "data": data}, status=201)


@require_role(ManagementRole.READ_ONLY)
async def statistics_handler(request: web.Request, ctx=None) -> web.Response:
    return web.json_response({"success": True, "data": vrs.statistics()})


@require_role(ManagementRole.ADMINISTRATOR)
async def for_ai_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = await vrs.for_ai_runtime(body)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def for_workflow_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = await vrs.for_workflow(body)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def for_service_builder_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = await vrs.for_service_builder(body)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def for_context_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    data = await vrs.for_context_engine(body)
    return web.json_response({"success": True, "data": data})


VOICE_ROUTE_SPECS: list[tuple[str, str, object]] = [
    ("GET", "", status_handler),
    ("GET", "status", status_handler),
    ("GET", "providers", providers_handler),
    ("POST", "sessions", sessions_create_handler),
    ("GET", "sessions", sessions_list_handler),
    ("GET", "sessions/{id}", sessions_get_handler),
    ("POST", "sessions/{id}/stop", sessions_stop_handler),
    ("POST", "sessions/{id}/mode", sessions_mode_handler),
    ("POST", "sessions/{id}/vad", vad_handler),
    ("POST", "sessions/{id}/wake", wake_handler),
    ("POST", "process", process_handler),
    ("POST", "parse", parse_handler),
    ("POST", "commands/{id}/confirm", confirm_handler),
    ("POST", "confirm", confirm_handler),
    ("GET", "commands", commands_handler),
    ("GET", "history", history_handler),
    ("GET", "devices", devices_list_handler),
    ("POST", "devices", devices_create_handler),
    ("GET", "profiles", profiles_list_handler),
    ("POST", "profiles", profiles_upsert_handler),
    ("GET", "statistics", statistics_handler),
    ("POST", "integrations/ai-runtime", for_ai_handler),
    ("POST", "integrations/workflow", for_workflow_handler),
    ("POST", "integrations/service-builder", for_service_builder_handler),
    ("POST", "integrations/context-engine", for_context_handler),
]


def _mount(app: web.Application, prefix: str, specs: list[tuple[str, str, object]]) -> None:
    for method, rel, handler in specs:
        rel = rel.strip("/")
        path = f"{prefix}/{rel}" if rel else prefix
        getattr(app.router, f"add_{method.lower()}")(path, handler)


def register_voice_runtime_routes(app: web.Application) -> None:
    from platform_api.versioning import MANAGEMENT_V1_PREFIX, register_dual_prefix_routes

    register_dual_prefix_routes(
        app,
        route_specs=VOICE_ROUTE_SPECS,  # type: ignore[arg-type]
        v1_prefix=f"{MANAGEMENT_V1_PREFIX}/voice",
        legacy_prefix="/management/voice",
    )
    _mount(app, "/api/voice", VOICE_ROUTE_SPECS)
    _mount(app, "/api/voice-runtime", VOICE_ROUTE_SPECS)
