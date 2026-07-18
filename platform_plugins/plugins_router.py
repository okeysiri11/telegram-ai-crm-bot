# Plugin Management API — /management/plugins/*

from __future__ import annotations

import logging
from typing import Any

from aiohttp import web

from platform_management.management_context import ManagementContext
from platform_management.permissions import ManagementRole, require_role
from platform_management.response_models import error_response, success_response
from platform_plugins.plugin_manager import plugin_manager

logger = logging.getLogger(__name__)


def _ok(data: Any, ctx: ManagementContext, *, status: int = 200) -> web.Response:
    return success_response(data, request_id=ctx.request_id, status=status)


async def _json_body(request: web.Request) -> dict[str, Any]:
    try:
        return await request.json()
    except Exception:
        return {}


async def _check_plugins_permission(ctx: ManagementContext, permission: str) -> web.Response | None:
    from platform_identity.identity_service import identity_service

    if ctx.actor_telegram_id is None:
        return error_response("actor required", request_id=ctx.request_id, status=403)
    principal = await identity_service.authenticate_telegram(ctx.actor_telegram_id)
    if not await identity_service.authorize(principal, permission):
        return error_response(
            f"Permission {permission} required",
            request_id=ctx.request_id,
            status=403,
        )
    return None


@require_role(ManagementRole.READ_ONLY)
async def plugins_list_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_plugins_permission(ctx, "plugins.read")
    if denied:
        return denied
    return _ok(await plugin_manager.list_plugins(), ctx)


@require_role(ManagementRole.READ_ONLY)
async def plugins_get_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_plugins_permission(ctx, "plugins.read")
    if denied:
        return denied
    plugin_id = request.match_info["plugin_id"]
    try:
        return _ok(await plugin_manager.get_plugin(plugin_id), ctx)
    except Exception as exc:
        return error_response(str(exc), request_id=ctx.request_id, status=404)


@require_role(ManagementRole.ADMINISTRATOR)
async def plugins_install_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_plugins_permission(ctx, "plugins.write")
    if denied:
        return denied
    body = await _json_body(request)
    plugin_id = body.get("plugin_id") or request.match_info.get("plugin_id")
    if not plugin_id:
        return error_response("plugin_id required", request_id=ctx.request_id, status=400)
    try:
        return _ok(await plugin_manager.install(str(plugin_id)), ctx)
    except Exception as exc:
        return error_response(str(exc), request_id=ctx.request_id, status=400)


@require_role(ManagementRole.ADMINISTRATOR)
async def plugins_enable_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_plugins_permission(ctx, "plugins.write")
    if denied:
        return denied
    plugin_id = request.match_info["plugin_id"]
    try:
        return _ok(await plugin_manager.enable(plugin_id), ctx)
    except Exception as exc:
        return error_response(str(exc), request_id=ctx.request_id, status=400)


@require_role(ManagementRole.ADMINISTRATOR)
async def plugins_disable_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_plugins_permission(ctx, "plugins.write")
    if denied:
        return denied
    plugin_id = request.match_info["plugin_id"]
    try:
        return _ok(await plugin_manager.disable(plugin_id), ctx)
    except Exception as exc:
        return error_response(str(exc), request_id=ctx.request_id, status=400)


@require_role(ManagementRole.ADMINISTRATOR)
async def plugins_reload_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_plugins_permission(ctx, "plugins.write")
    if denied:
        return denied
    plugin_id = request.match_info.get("plugin_id")
    try:
        return _ok(await plugin_manager.reload(plugin_id), ctx)
    except Exception as exc:
        return error_response(str(exc), request_id=ctx.request_id, status=400)


@require_role(ManagementRole.ADMINISTRATOR)
async def plugins_uninstall_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_plugins_permission(ctx, "plugins.write")
    if denied:
        return denied
    plugin_id = request.match_info["plugin_id"]
    try:
        return _ok(await plugin_manager.uninstall(plugin_id), ctx)
    except Exception as exc:
        return error_response(str(exc), request_id=ctx.request_id, status=400)


@require_role(ManagementRole.ADMINISTRATOR)
async def plugins_upgrade_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_plugins_permission(ctx, "plugins.write")
    if denied:
        return denied
    plugin_id = request.match_info["plugin_id"]
    try:
        return _ok(await plugin_manager.upgrade(plugin_id), ctx)
    except Exception as exc:
        return error_response(str(exc), request_id=ctx.request_id, status=400)


@require_role(ManagementRole.READ_ONLY)
async def plugins_health_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_plugins_permission(ctx, "plugins.read")
    if denied:
        return denied
    plugin_id = request.match_info.get("plugin_id")
    return _ok(await plugin_manager.health(plugin_id), ctx)


@require_role(ManagementRole.READ_ONLY)
async def plugins_dependencies_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_plugins_permission(ctx, "plugins.read")
    if denied:
        return denied
    return _ok(await plugin_manager.dependencies(), ctx)


@require_role(ManagementRole.READ_ONLY)
async def plugins_schema_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_plugins_permission(ctx, "plugins.read")
    if denied:
        return denied
    return _ok(plugin_manager.manifest_schema(), ctx)


def register_plugins_routes(app: web.Application) -> None:
    from platform_api.versioning import MANAGEMENT_V1_PREFIX, register_dual_prefix_routes

    route_specs = [
        ("GET", "", plugins_list_handler),
        ("GET", "schema", plugins_schema_handler),
        ("GET", "dependencies", plugins_dependencies_handler),
        ("GET", "health", plugins_health_handler),
        ("POST", "install", plugins_install_handler),
        ("POST", "reload", plugins_reload_handler),
        ("GET", "{plugin_id}", plugins_get_handler),
        ("POST", "{plugin_id}/install", plugins_install_handler),
        ("POST", "{plugin_id}/enable", plugins_enable_handler),
        ("POST", "{plugin_id}/disable", plugins_disable_handler),
        ("POST", "{plugin_id}/reload", plugins_reload_handler),
        ("POST", "{plugin_id}/upgrade", plugins_upgrade_handler),
        ("POST", "{plugin_id}/uninstall", plugins_uninstall_handler),
        ("GET", "{plugin_id}/health", plugins_health_handler),
    ]
    register_dual_prefix_routes(
        app,
        route_specs=route_specs,
        v1_prefix=f"{MANAGEMENT_V1_PREFIX}/plugins",
        legacy_prefix="/management/plugins",
    )
    logger.info("plugins_api_routes_registered v1=%s/plugins", MANAGEMENT_V1_PREFIX)
