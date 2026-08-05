"""Enterprise Service Builder HTTP API — Sprint 36.0.

Primary: /api/service-builder/*
Also: /management/v1/service-builder/* (+ legacy /management/service-builder/*)
"""

from __future__ import annotations

from aiohttp import web

from platform_management.permissions import ManagementRole, require_role
from platform_service_builder.lifecycle import LifecycleError
from platform_service_builder.permissions import ServicePermissionDenied
from platform_service_builder.service import service_builder


def _actor(request: web.Request) -> str:
    return (
        request.headers.get("X-Actor-Id")
        or request.get("user_id")
        or request.query.get("actor")
        or "system"
    )


def _error(exc: Exception, *, status: int = 400) -> web.Response:
    return web.json_response(
        {"success": False, "error": str(exc), "errors": [str(exc)]},
        status=status,
    )


@require_role(ManagementRole.READ_ONLY)
async def sb_status_handler(request: web.Request, ctx=None) -> web.Response:
    return web.json_response({"success": True, "data": service_builder.status()})


@require_role(ManagementRole.READ_ONLY)
async def sb_list_handler(request: web.Request, ctx=None) -> web.Response:
    services = service_builder.list_services(
        state=request.query.get("state"),
        category=request.query.get("category"),
        installed_only=request.query.get("installed") == "1",
        running_only=request.query.get("running") == "1",
    )
    return web.json_response({
        "success": True,
        "data": {
            "services": [s.to_dict() for s in services],
            "count": len(services),
        },
    })


@require_role(ManagementRole.READ_ONLY)
async def sb_get_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        service = service_builder.get(request.match_info["id"])
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": service.to_dict()})


@require_role(ManagementRole.ADMINISTRATOR)
async def sb_create_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    try:
        service = service_builder.create(body, actor=_actor(request))
    except ValueError as exc:
        return _error(exc, status=409)
    return web.json_response({"success": True, "data": service.to_dict()}, status=201)


@require_role(ManagementRole.ADMINISTRATOR)
async def sb_update_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    try:
        service = service_builder.update(request.match_info["id"], body, actor=_actor(request))
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": service.to_dict()})


@require_role(ManagementRole.ADMINISTRATOR)
async def sb_delete_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        data = service_builder.delete(request.match_info["id"], actor=_actor(request))
    except (KeyError, LifecycleError) as exc:
        status = 404 if isinstance(exc, KeyError) else 409
        return _error(exc, status=status)
    return web.json_response({"success": True, "data": data})


async def _lifecycle(request: web.Request, op: str) -> web.Response:
    sid = request.match_info["id"]
    actor = _actor(request)
    try:
        fn = getattr(service_builder, op)
        service = fn(sid, actor=actor)
    except KeyError as exc:
        return _error(exc, status=404)
    except LifecycleError as exc:
        return _error(exc, status=409)
    except Exception as exc:
        return _error(exc, status=500)
    return web.json_response({"success": True, "data": service.to_dict()})


@require_role(ManagementRole.ADMINISTRATOR)
async def sb_install_handler(request: web.Request, ctx=None) -> web.Response:
    return await _lifecycle(request, "install")


@require_role(ManagementRole.ADMINISTRATOR)
async def sb_load_handler(request: web.Request, ctx=None) -> web.Response:
    return await _lifecycle(request, "load")


@require_role(ManagementRole.ADMINISTRATOR)
async def sb_start_handler(request: web.Request, ctx=None) -> web.Response:
    return await _lifecycle(request, "start")


@require_role(ManagementRole.ADMINISTRATOR)
async def sb_stop_handler(request: web.Request, ctx=None) -> web.Response:
    return await _lifecycle(request, "stop")


@require_role(ManagementRole.ADMINISTRATOR)
async def sb_restart_handler(request: web.Request, ctx=None) -> web.Response:
    return await _lifecycle(request, "restart")


@require_role(ManagementRole.ADMINISTRATOR)
async def sb_reload_handler(request: web.Request, ctx=None) -> web.Response:
    return await _lifecycle(request, "reload")


@require_role(ManagementRole.ADMINISTRATOR)
async def sb_enable_handler(request: web.Request, ctx=None) -> web.Response:
    return await _lifecycle(request, "enable")


@require_role(ManagementRole.ADMINISTRATOR)
async def sb_disable_handler(request: web.Request, ctx=None) -> web.Response:
    return await _lifecycle(request, "disable")


@require_role(ManagementRole.READ_ONLY)
async def sb_health_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        data = service_builder.health_of(request.match_info["id"])
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.READ_ONLY)
async def sb_health_monitor_handler(request: web.Request, ctx=None) -> web.Response:
    return web.json_response({"success": True, "data": {"services": service_builder.health_monitor()}})


@require_role(ManagementRole.READ_ONLY)
async def sb_logs_handler(request: web.Request, ctx=None) -> web.Response:
    limit = int(request.query.get("limit") or 100)
    try:
        data = service_builder.logs(request.match_info["id"], limit=limit)
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": {"logs": data, "count": len(data)}})


@require_role(ManagementRole.READ_ONLY)
async def sb_dependencies_handler(request: web.Request, ctx=None) -> web.Response:
    sid = request.match_info.get("id")
    return web.json_response({"success": True, "data": service_builder.dependency_graph(sid)})


@require_role(ManagementRole.READ_ONLY)
async def sb_versions_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        data = service_builder.versions(request.match_info["id"])
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": {"versions": data}})


@require_role(ManagementRole.READ_ONLY)
async def sb_permissions_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        data = service_builder.permissions_of(request.match_info["id"])
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def sb_configure_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    try:
        service = service_builder.configure(
            request.match_info["id"],
            body.get("configuration") or body,
            actor=_actor(request),
        )
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": service.to_dict()})


@require_role(ManagementRole.READ_ONLY)
async def sb_permission_check_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        data = service_builder.check_permission(
            request.match_info["id"],
            api=request.query.get("api"),
            event=request.query.get("event"),
            storage=request.query.get("storage"),
            ai_tool=request.query.get("ai_tool"),
            integration=request.query.get("integration"),
        )
    except (KeyError, ServicePermissionDenied) as exc:
        status = 404 if isinstance(exc, KeyError) else 403
        return _error(exc, status=status)
    return web.json_response({"success": True, "data": data})


ROUTE_SPECS: list[tuple[str, str, object]] = [
    ("GET", "", sb_status_handler),
    ("GET", "services", sb_list_handler),
    ("GET", "services/{id}", sb_get_handler),
    ("POST", "services", sb_create_handler),
    ("PUT", "services/{id}", sb_update_handler),
    ("DELETE", "services/{id}", sb_delete_handler),
    ("POST", "services/{id}/install", sb_install_handler),
    ("POST", "services/{id}/load", sb_load_handler),
    ("POST", "services/{id}/start", sb_start_handler),
    ("POST", "services/{id}/stop", sb_stop_handler),
    ("POST", "services/{id}/restart", sb_restart_handler),
    ("POST", "services/{id}/reload", sb_reload_handler),
    ("POST", "services/{id}/enable", sb_enable_handler),
    ("POST", "services/{id}/disable", sb_disable_handler),
    ("POST", "services/{id}/configure", sb_configure_handler),
    ("GET", "services/{id}/health", sb_health_handler),
    ("GET", "services/{id}/logs", sb_logs_handler),
    ("GET", "services/{id}/versions", sb_versions_handler),
    ("GET", "services/{id}/permissions", sb_permissions_handler),
    ("GET", "services/{id}/permissions/check", sb_permission_check_handler),
    ("GET", "services/{id}/dependencies", sb_dependencies_handler),
    ("GET", "dependencies", sb_dependencies_handler),
    ("GET", "health", sb_health_monitor_handler),
]


def register_service_builder_routes(app: web.Application) -> None:
    from platform_api.versioning import MANAGEMENT_V1_PREFIX, register_dual_prefix_routes

    # Management dual-prefix (platform standard)
    register_dual_prefix_routes(
        app,
        route_specs=ROUTE_SPECS,  # type: ignore[arg-type]
        v1_prefix=f"{MANAGEMENT_V1_PREFIX}/service-builder",
        legacy_prefix="/management/service-builder",
    )

    # Product path requested by Sprint 36.0: /api/service-builder
    for method, rel, handler in ROUTE_SPECS:
        rel = rel.strip("/")
        path = f"/api/service-builder/{rel}" if rel else "/api/service-builder"
        getattr(app.router, f"add_{method.lower()}")(path, handler)
