# Job Engine Management API — /management/jobs/*

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from aiohttp import web

from platform_jobs.job_engine import job_engine
from platform_jobs.models import JobType
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


async def _check_jobs_permission(ctx: ManagementContext, permission: str) -> web.Response | None:
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
async def jobs_status_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_jobs_permission(ctx, "jobs.read")
    if denied:
        return denied
    return _ok(await job_engine.status(), ctx)


@require_role(ManagementRole.READ_ONLY)
async def jobs_scheduler_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_jobs_permission(ctx, "jobs.read")
    if denied:
        return denied
    status = await job_engine.status()
    return _ok(status["scheduler"], ctx)


@require_role(ManagementRole.READ_ONLY)
async def jobs_workers_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_jobs_permission(ctx, "jobs.read")
    if denied:
        return denied
    status = await job_engine.status()
    return _ok(status["workers"], ctx)


@require_role(ManagementRole.READ_ONLY)
async def jobs_history_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_jobs_permission(ctx, "jobs.read")
    if denied:
        return denied
    status = await job_engine.status()
    return _ok({"history": status["history"], "retry_history": status["retry_history"]}, ctx)


@require_role(ManagementRole.READ_ONLY)
async def jobs_statistics_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_jobs_permission(ctx, "jobs.read")
    if denied:
        return denied
    status = await job_engine.status()
    return _ok(status["metrics"], ctx)


@require_role(ManagementRole.ADMINISTRATOR)
async def jobs_enqueue_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_jobs_permission(ctx, "jobs.write")
    if denied:
        return denied
    body = await _json_body(request)
    handler_name = str(body.get("handler_name", ""))
    if not handler_name:
        return error_response("handler_name required", request_id=ctx.request_id, status=400)

    job_type_str = str(body.get("job_type", "immediate"))
    try:
        job_type = JobType(job_type_str)
    except ValueError:
        return error_response(f"Invalid job_type: {job_type_str}", request_id=ctx.request_id, status=400)

    run_at = None
    if body.get("run_at"):
        run_at = datetime.fromisoformat(body["run_at"])
        if run_at.tzinfo is None:
            run_at = run_at.replace(tzinfo=timezone.utc)

    job = await job_engine.enqueue(
        handler_name,
        dict(body.get("payload", {})),
        job_type=job_type,
        priority=int(body.get("priority", 5)),
        max_retries=int(body.get("max_retries", 5)),
        delay_seconds=body.get("delay_seconds"),
        run_at=run_at,
        cron_expression=body.get("cron_expression"),
        interval_seconds=body.get("interval_seconds"),
        pipeline_steps=body.get("pipeline_steps"),
        tz=str(body.get("timezone", "UTC")),
    )
    return _ok({"job": job.to_dict()}, ctx, status=201)


@require_role(ManagementRole.ADMINISTRATOR)
async def jobs_cancel_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_jobs_permission(ctx, "jobs.write")
    if denied:
        return denied
    job_id = request.match_info["job_id"]
    body = await _json_body(request)
    try:
        job = await job_engine.cancel(job_id, reason=str(body.get("reason", "")))
    except Exception as exc:
        return error_response(str(exc), request_id=ctx.request_id, status=404)
    return _ok({"job": job.to_dict()}, ctx)


@require_role(ManagementRole.READ_ONLY)
async def jobs_dashboard_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_jobs_permission(ctx, "jobs.read")
    if denied:
        return denied
    return _ok(await job_engine.dashboard_widgets(), ctx)


def register_jobs_routes(app: web.Application) -> None:
    from platform_api.versioning import MANAGEMENT_V1_PREFIX, register_dual_prefix_routes

    route_specs = [
        ("GET", "", jobs_status_handler),
        ("GET", "scheduler", jobs_scheduler_handler),
        ("GET", "workers", jobs_workers_handler),
        ("GET", "history", jobs_history_handler),
        ("GET", "statistics", jobs_statistics_handler),
        ("GET", "dashboard", jobs_dashboard_handler),
        ("POST", "", jobs_enqueue_handler),
        ("POST", "{job_id}/cancel", jobs_cancel_handler),
    ]
    register_dual_prefix_routes(
        app,
        route_specs=route_specs,
        v1_prefix=f"{MANAGEMENT_V1_PREFIX}/jobs",
        legacy_prefix="/management/jobs",
    )
    logger.info("jobs_api_routes_registered v1=%s/jobs", MANAGEMENT_V1_PREFIX)
