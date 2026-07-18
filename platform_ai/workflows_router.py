# AI Workflows Management API — /management/ai/workflows/*

from __future__ import annotations

import logging
from typing import Any

from aiohttp import web

from platform_ai.workflows.models import WorkflowExecutionRequest
from platform_ai.workflows.workflow_engine import ai_workflow_engine
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
async def workflows_status_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_ai_permission(ctx, "ai.read")
    if denied:
        return denied
    return _ok(
        {
            "summary": ai_workflow_engine.summary(),
            "active": ai_workflow_engine.active(),
            "metrics": ai_workflow_engine.metrics(),
        },
        ctx,
    )


@require_role(ManagementRole.READ_ONLY)
async def workflows_list_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_ai_permission(ctx, "ai.read")
    if denied:
        return denied
    return _ok({"workflows": ai_workflow_engine.list_workflows()}, ctx)


@require_role(ManagementRole.READ_ONLY)
async def workflows_templates_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_ai_permission(ctx, "ai.read")
    if denied:
        return denied
    return _ok({"templates": ai_workflow_engine.list_templates()}, ctx)


@require_role(ManagementRole.READ_ONLY)
async def workflows_history_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_ai_permission(ctx, "ai.read")
    if denied:
        return denied
    limit = int(request.query.get("limit", 50))
    return _ok({"history": ai_workflow_engine.history(limit)}, ctx)


@require_role(ManagementRole.READ_ONLY)
async def workflows_metrics_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_ai_permission(ctx, "ai.read")
    if denied:
        return denied
    workflow_id = request.match_info.get("workflow_id") or request.query.get("workflow_id")
    return _ok(ai_workflow_engine.metrics(workflow_id), ctx)


@require_role(ManagementRole.ADMINISTRATOR)
async def workflows_execute_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_ai_permission(ctx, "ai.use")
    if denied:
        return denied
    body = await _json_body(request)
    workflow_id = body.get("workflow_id") or request.match_info.get("workflow_id")
    if not workflow_id:
        return error_response("workflow_id required", request_id=ctx.request_id, status=400)
    exec_request = WorkflowExecutionRequest(
        workflow_id=workflow_id,
        input=body.get("input", {}),
        plugin_id=body.get("plugin_id"),
        user_id=body.get("user_id") or (str(ctx.actor_telegram_id) if ctx.actor_telegram_id else None),
        use_cache=body.get("use_cache", True),
    )
    try:
        result = await ai_workflow_engine.execute(exec_request)
        return _ok(result.to_dict(), ctx)
    except Exception as exc:
        return error_response(str(exc), request_id=ctx.request_id, status=502)


@require_role(ManagementRole.ADMINISTRATOR)
async def workflows_cancel_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_ai_permission(ctx, "ai.admin")
    if denied:
        return denied
    execution_id = request.match_info.get("execution_id")
    if not execution_id:
        return error_response("execution_id required", request_id=ctx.request_id, status=400)
    cancelled = ai_workflow_engine.cancel(execution_id)
    return _ok({"cancelled": cancelled, "execution_id": execution_id}, ctx)


@require_role(ManagementRole.ADMINISTRATOR)
async def workflows_resume_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_ai_permission(ctx, "ai.use")
    if denied:
        return denied
    execution_id = request.match_info.get("execution_id")
    if not execution_id:
        return error_response("execution_id required", request_id=ctx.request_id, status=400)
    try:
        result = await ai_workflow_engine.resume(execution_id)
        return _ok(result.to_dict(), ctx)
    except Exception as exc:
        return error_response(str(exc), request_id=ctx.request_id, status=502)


def register_workflows_routes(app: web.Application) -> None:
    from platform_api.versioning import MANAGEMENT_V1_PREFIX, register_dual_prefix_routes

    route_specs = [
        ("GET", "", workflows_status_handler),
        ("GET", "list", workflows_list_handler),
        ("GET", "templates", workflows_templates_handler),
        ("GET", "history", workflows_history_handler),
        ("GET", "metrics", workflows_metrics_handler),
        ("GET", "metrics/{workflow_id}", workflows_metrics_handler),
        ("POST", "execute", workflows_execute_handler),
        ("POST", "execute/{workflow_id}", workflows_execute_handler),
        ("POST", "{execution_id}/cancel", workflows_cancel_handler),
        ("POST", "{execution_id}/resume", workflows_resume_handler),
    ]
    register_dual_prefix_routes(
        app,
        route_specs=route_specs,
        v1_prefix=f"{MANAGEMENT_V1_PREFIX}/ai/workflows",
        legacy_prefix="/management/ai/workflows",
    )
    logger.info("workflows_api_routes_registered v1=%s/ai/workflows", MANAGEMENT_V1_PREFIX)
