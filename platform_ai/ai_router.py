# AI Management API — /management/ai/*

from __future__ import annotations

import logging
from typing import Any

from aiohttp import web

from platform_ai.ai_service import ai_service
from platform_ai.cache import ai_cache
from platform_ai.cost_tracker import cost_tracker
from platform_ai.model_registry import model_registry
from platform_ai.models import AIRequest, TaskType
from platform_ai.prompt_service import prompt_service
from platform_ai.provider_manager import provider_manager
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


async def _check_ai_permission(ctx: ManagementContext, permission: str) -> web.Response | None:
    from platform_identity.identity_service import identity_service

    if ctx.actor_telegram_id is None:
        return error_response("actor required", request_id=ctx.request_id, status=403)
    principal = await identity_service.authenticate_telegram(ctx.actor_telegram_id)
    if not await identity_service.authorize(principal, permission):
        return error_response(f"Permission {permission} required", request_id=ctx.request_id, status=403)
    return None


@require_role(ManagementRole.READ_ONLY)
async def ai_status_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_ai_permission(ctx, "ai.read")
    if denied:
        return denied
    return _ok(await ai_service.status(), ctx)


@require_role(ManagementRole.READ_ONLY)
async def ai_providers_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_ai_permission(ctx, "ai.read")
    if denied:
        return denied
    ai_service.initialize()
    providers = await provider_manager.health_all()
    return _ok({"providers": [p.to_dict() for p in providers]}, ctx)


@require_role(ManagementRole.READ_ONLY)
async def ai_models_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_ai_permission(ctx, "ai.read")
    if denied:
        return denied
    ai_service.initialize()
    return _ok({"models": [m.to_dict() for m in model_registry.list_all()]}, ctx)


@require_role(ManagementRole.READ_ONLY)
async def ai_prompts_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_ai_permission(ctx, "ai.read")
    if denied:
        return denied
    ai_service.initialize()
    return _ok({"prompts": [t.to_dict() for t in prompt_service.list_templates()]}, ctx)


@require_role(ManagementRole.READ_ONLY)
async def ai_statistics_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_ai_permission(ctx, "ai.read")
    if denied:
        return denied
    ai_service.initialize()
    providers = await provider_manager.health_all()
    return _ok(
        {
            "request_count": ai_service._request_count,
            "providers": [{"id": p.provider_id, "latency_ms": p.latency_ms, "status": p.status.value} for p in providers],
            "cache": ai_cache.stats(),
        },
        ctx,
    )


@require_role(ManagementRole.READ_ONLY)
async def ai_costs_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_ai_permission(ctx, "ai.read")
    if denied:
        return denied
    return _ok({"summary": cost_tracker.summary(), "recent": cost_tracker.recent()}, ctx)


@require_role(ManagementRole.ADMINISTRATOR)
async def ai_cache_invalidate_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_ai_permission(ctx, "ai.admin")
    if denied:
        return denied
    body = await _json_body(request)
    removed = ai_cache.invalidate(body.get("provider_id"), body.get("model_id"))
    return _ok({"invalidated": removed}, ctx)


@require_role(ManagementRole.ADMINISTRATOR)
async def ai_complete_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_ai_permission(ctx, "ai.use")
    if denied:
        return denied
    body = await _json_body(request)
    ai_request = AIRequest(
        prompt=body.get("prompt", ""),
        task_type=TaskType(body.get("task_type", TaskType.CHAT.value)),
        provider=body.get("provider"),
        model=body.get("model"),
        plugin_id=body.get("plugin_id"),
        template_id=body.get("template_id"),
        template_vars=body.get("template_vars", {}),
        context=body.get("context", {}),
        max_tokens=int(body.get("max_tokens", 1024)),
        use_cache=body.get("use_cache", True),
    )
    try:
        response = await ai_service.complete(ai_request)
        return _ok(response.to_dict(), ctx)
    except Exception as exc:
        return error_response(str(exc), request_id=ctx.request_id, status=502)


def register_ai_routes(app: web.Application) -> None:
    prefix = "/management/ai"

    app.router.add_get(prefix, ai_status_handler)
    app.router.add_get(f"{prefix}/providers", ai_providers_handler)
    app.router.add_get(f"{prefix}/models", ai_models_handler)
    app.router.add_get(f"{prefix}/prompts", ai_prompts_handler)
    app.router.add_get(f"{prefix}/statistics", ai_statistics_handler)
    app.router.add_get(f"{prefix}/costs", ai_costs_handler)
    app.router.add_get(f"{prefix}/cache", ai_statistics_handler)
    app.router.add_post(f"{prefix}/cache/invalidate", ai_cache_invalidate_handler)
    app.router.add_post(f"{prefix}/complete", ai_complete_handler)

    logger.info("ai_api_routes_registered prefix=%s", prefix)
