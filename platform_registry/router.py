# Platform Registry HTTP API — Sprint 34.2B.

from __future__ import annotations

from aiohttp import web

from platform_management.permissions import ManagementRole, require_role
from platform_registry.service import platform_registry


@require_role(ManagementRole.READ_ONLY)
async def platform_registry_snapshot_handler(request: web.Request) -> web.Response:
    return web.json_response({"success": True, "data": platform_registry.snapshot()})


@require_role(ManagementRole.READ_ONLY)
async def platform_registry_navigation_handler(request: web.Request) -> web.Response:
    client = str(request.query.get("client") or "web").lower()
    roles_raw = str(request.query.get("roles") or "")
    roles = [r.strip() for r in roles_raw.split(",") if r.strip()]
    include_owner = str(request.query.get("owner") or "").lower() in {"1", "true", "yes"}
    simple = str(request.query.get("simple") or "").lower() in {"1", "true", "yes"}
    data = platform_registry.navigation_for(
        client=client,
        roles=roles or None,
        include_owner=include_owner,
        simple=simple,
    )
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.READ_ONLY)
async def platform_registry_menus_handler(request: web.Request) -> web.Response:
    snap = platform_registry.snapshot()
    return web.json_response({"success": True, "data": {"menus": snap["menus"]}})


@require_role(ManagementRole.READ_ONLY)
async def platform_registry_verticals_handler(request: web.Request) -> web.Response:
    snap = platform_registry.snapshot()
    return web.json_response({"success": True, "data": {"verticals": snap["verticals"]}})


@require_role(ManagementRole.READ_ONLY)
async def platform_registry_agents_handler(request: web.Request) -> web.Response:
    snap = platform_registry.snapshot()
    return web.json_response({"success": True, "data": {"agents": snap["agents"]}})


def register_platform_registry_routes(app: web.Application) -> None:
    from platform_api.versioning import MANAGEMENT_V1_PREFIX, register_dual_prefix_routes

    route_specs = [
        ("GET", "", platform_registry_snapshot_handler),
        ("GET", "navigation", platform_registry_navigation_handler),
        ("GET", "menus", platform_registry_menus_handler),
        ("GET", "verticals", platform_registry_verticals_handler),
        ("GET", "agents", platform_registry_agents_handler),
    ]
    register_dual_prefix_routes(
        app,
        route_specs=route_specs,
        v1_prefix=f"{MANAGEMENT_V1_PREFIX}/platform-registry",
        legacy_prefix="/management/platform-registry",
    )
