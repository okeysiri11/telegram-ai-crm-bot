# Integration Hub Management API — /management/integrations/*

from __future__ import annotations

import logging
from typing import Any

from aiohttp import web

from platform_integrations.integration_service import integration_service
from platform_integrations.provider_manager import provider_manager
from platform_management.management_context import ManagementContext
from platform_management.permissions import ManagementRole, require_role
from platform_management.response_models import error_response, success_response

logger = logging.getLogger(__name__)


def _ok(data: Any, ctx: ManagementContext, *, status: int = 200) -> web.Response:
    return success_response(data, request_id=ctx.request_id, status=status)


async def _json_body(request: web.Request) -> dict[str, Any]:
    try:
        return await request.json()
    except Exception:
        return {}


async def _check_integration_permission(ctx: ManagementContext, permission: str) -> web.Response | None:
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
async def integrations_status_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_integration_permission(ctx, "integrations.read")
    if denied:
        return denied
    integration_service.bootstrap()
    return _ok(integration_service.status(), ctx)


@require_role(ManagementRole.READ_ONLY)
async def integrations_connectors_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_integration_permission(ctx, "integrations.read")
    if denied:
        return denied
    integration_service.bootstrap()
    return _ok({"connectors": integration_service.status()["connectors"]}, ctx)


@require_role(ManagementRole.ADMINISTRATOR)
async def integrations_connector_enable_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_integration_permission(ctx, "integrations.write")
    if denied:
        return denied
    connector_id = request.match_info["connector_id"]
    meta = provider_manager.enable(connector_id)
    await provider_manager.connect(connector_id)
    return _ok({"connector": meta.to_dict()}, ctx)


@require_role(ManagementRole.ADMINISTRATOR)
async def integrations_connector_disable_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_integration_permission(ctx, "integrations.write")
    if denied:
        return denied
    connector_id = request.match_info["connector_id"]
    meta = provider_manager.disable(connector_id)
    return _ok({"connector": meta.to_dict()}, ctx)


@require_role(ManagementRole.READ_ONLY)
async def integrations_webhooks_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_integration_permission(ctx, "integrations.read")
    if denied:
        return denied
    return _ok({"webhooks": integration_service.status()["webhooks"]}, ctx)


@require_role(ManagementRole.ADMINISTRATOR)
async def integrations_webhooks_create_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_integration_permission(ctx, "integrations.write")
    if denied:
        return denied
    body = await _json_body(request)
    reg = integration_service.register_webhook(
        name=str(body.get("name", "webhook")),
        provider=str(body.get("provider", "webhook")),
        connector_id=body.get("connector_id"),
    )
    return _ok({"webhook": reg.to_dict(include_secret=True)}, ctx, status=201)


@require_role(ManagementRole.READ_ONLY)
async def integrations_health_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_integration_permission(ctx, "integrations.read")
    if denied:
        return denied
    integration_service.bootstrap()
    return _ok(await integration_service.health(), ctx)


@require_role(ManagementRole.READ_ONLY)
async def integrations_statistics_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_integration_permission(ctx, "integrations.read")
    if denied:
        return denied
    return _ok(integration_service.status()["statistics"], ctx)


def register_integration_routes(app: web.Application) -> None:
    prefix = "/management/integrations"

    app.router.add_get(prefix, integrations_status_handler)
    app.router.add_get(f"{prefix}/connectors", integrations_connectors_handler)
    app.router.add_post(f"{prefix}/connectors/{{connector_id}}/enable", integrations_connector_enable_handler)
    app.router.add_post(f"{prefix}/connectors/{{connector_id}}/disable", integrations_connector_disable_handler)
    app.router.add_get(f"{prefix}/webhooks", integrations_webhooks_handler)
    app.router.add_post(f"{prefix}/webhooks", integrations_webhooks_create_handler)
    app.router.add_get(f"{prefix}/health", integrations_health_handler)
    app.router.add_get(f"{prefix}/statistics", integrations_statistics_handler)

    from platform_integrations.webhook_router import register_webhook_routes

    register_webhook_routes(app)

    logger.info("integration_api_routes_registered prefix=%s", prefix)
