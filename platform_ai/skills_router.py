# AI Skills Management API — /management/ai/skills/*

from __future__ import annotations

import logging
from typing import Any

from aiohttp import web

from platform_ai.skills.models import SkillExecutionRequest
from platform_ai.skills.skill_manager import skill_manager
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
        return error_response("permission denied", request_id=ctx.request_id, status=403)
    return None


@require_role(ManagementRole.READ_ONLY)
async def skills_status_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_ai_permission(ctx, "ai.read")
    if denied:
        return denied
    return _ok({"summary": skill_manager.summary(), "health": await skill_manager.health()}, ctx)


@require_role(ManagementRole.READ_ONLY)
async def skills_list_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_ai_permission(ctx, "ai.read")
    if denied:
        return denied
    return _ok({"skills": skill_manager.list_skills()}, ctx)


@require_role(ManagementRole.READ_ONLY)
async def skills_metrics_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_ai_permission(ctx, "ai.read")
    if denied:
        return denied
    skill_id = request.match_info.get("skill_id") or request.query.get("skill_id")
    return _ok(skill_manager.metrics(skill_id), ctx)


@require_role(ManagementRole.READ_ONLY)
async def skills_health_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_ai_permission(ctx, "ai.read")
    if denied:
        return denied
    skill_id = request.match_info.get("skill_id") or request.query.get("skill_id")
    return _ok(await skill_manager.health(skill_id), ctx)


@require_role(ManagementRole.ADMINISTRATOR)
async def skills_execute_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_ai_permission(ctx, "ai.use")
    if denied:
        return denied
    body = await _json_body(request)
    skill_id = body.get("skill_id") or request.match_info.get("skill_id")
    if not skill_id:
        return error_response("skill_id required", request_id=ctx.request_id, status=400)
    exec_request = SkillExecutionRequest(
        skill_id=skill_id,
        input=body.get("input", {}),
        plugin_id=body.get("plugin_id"),
        user_id=body.get("user_id") or (str(ctx.actor_telegram_id) if ctx.actor_telegram_id else None),
        use_cache=body.get("use_cache", True),
    )
    try:
        result = await skill_manager.execute(exec_request, extra_context=body.get("context"))
        return _ok(result.to_dict(), ctx)
    except Exception as exc:
        return error_response(str(exc), request_id=ctx.request_id, status=502)


@require_role(ManagementRole.ADMINISTRATOR)
async def skills_disable_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_ai_permission(ctx, "ai.admin")
    if denied:
        return denied
    skill_id = request.match_info.get("skill_id")
    if not skill_id:
        return error_response("skill_id required", request_id=ctx.request_id, status=400)
    record = await skill_manager.disable(skill_id)
    return _ok(record.to_dict(), ctx)


@require_role(ManagementRole.ADMINISTRATOR)
async def skills_enable_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_ai_permission(ctx, "ai.admin")
    if denied:
        return denied
    skill_id = request.match_info.get("skill_id")
    if not skill_id:
        return error_response("skill_id required", request_id=ctx.request_id, status=400)
    record = await skill_manager.enable(skill_id)
    return _ok(record.to_dict(), ctx)


def register_skills_routes(app: web.Application) -> None:
    from platform_api.versioning import MANAGEMENT_V1_PREFIX, register_dual_prefix_routes

    route_specs = [
        ("GET", "", skills_status_handler),
        ("GET", "list", skills_list_handler),
        ("GET", "metrics", skills_metrics_handler),
        ("GET", "metrics/{skill_id}", skills_metrics_handler),
        ("GET", "health", skills_health_handler),
        ("GET", "health/{skill_id}", skills_health_handler),
        ("POST", "execute", skills_execute_handler),
        ("POST", "execute/{skill_id}", skills_execute_handler),
        ("POST", "{skill_id}/disable", skills_disable_handler),
        ("POST", "{skill_id}/enable", skills_enable_handler),
    ]
    register_dual_prefix_routes(
        app,
        route_specs=route_specs,
        v1_prefix=f"{MANAGEMENT_V1_PREFIX}/ai/skills",
        legacy_prefix="/management/ai/skills",
    )
    logger.info("skills_api_routes_registered v1=%s/ai/skills", MANAGEMENT_V1_PREFIX)
