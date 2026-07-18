# Telemetry router — Management API /management/observability/*

from __future__ import annotations

import logging
from typing import Any

from aiohttp import web

from platform_observability.alert_manager import alert_manager
from platform_observability.dashboard_metrics import all_dashboard_widgets, status_snapshot
from platform_observability.health_monitor import health_monitor
from platform_observability.logging_service import logging_service
from platform_observability.metrics_service import metrics_service
from platform_observability.models import AlertSeverity
from platform_observability.retention_manager import retention_manager
from platform_observability.tracing_service import tracing_service
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


async def _check_obs_permission(ctx: ManagementContext, permission: str) -> web.Response | None:
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
async def observability_status_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_obs_permission(ctx, "observability.read")
    if denied:
        return denied
    return _ok(await status_snapshot(), ctx)


@require_role(ManagementRole.READ_ONLY)
async def observability_metrics_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_obs_permission(ctx, "observability.read")
    if denied:
        return denied
    await metrics_service.collect_platform_metrics()
    name = request.query.get("name")
    return _ok(
        {
            "catalog": metrics_service.catalog(),
            "summary": metrics_service.summary(),
            "points": metrics_service.query(name=name, limit=int(request.query.get("limit", "200"))),
        },
        ctx,
    )


@require_role(ManagementRole.READ_ONLY)
async def observability_logs_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_obs_permission(ctx, "observability.read")
    if denied:
        return denied
    return _ok(
        {
            "logs": logging_service.query(
                level=request.query.get("level"),
                correlation_id=request.query.get("correlation_id"),
                component=request.query.get("component"),
                limit=int(request.query.get("limit", "200")),
            )
        },
        ctx,
    )


@require_role(ManagementRole.READ_ONLY)
async def observability_traces_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_obs_permission(ctx, "observability.read")
    if denied:
        return denied
    trace_id = request.query.get("trace_id")
    if trace_id:
        return _ok({"trace": tracing_service.get_trace(trace_id)}, ctx)
    return _ok(
        {
            "spans": tracing_service.query(
                component=request.query.get("component"),
                limit=int(request.query.get("limit", "200")),
            ),
            "slowest": tracing_service.slowest(),
        },
        ctx,
    )


@require_role(ManagementRole.READ_ONLY)
async def observability_alerts_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_obs_permission(ctx, "observability.read")
    if denied:
        return denied
    return _ok(
        {"alerts": [a.to_dict() for a in alert_manager.list_alerts()]},
        ctx,
    )


@require_role(ManagementRole.ADMINISTRATOR)
async def observability_alerts_resolve_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_obs_permission(ctx, "observability.write")
    if denied:
        return denied
    alert_id = request.match_info["alert_id"]
    try:
        alert = await alert_manager.resolve(alert_id)
    except KeyError as exc:
        return error_response(str(exc), request_id=ctx.request_id, status=404)
    return _ok({"alert": alert.to_dict()}, ctx)


@require_role(ManagementRole.READ_ONLY)
async def observability_health_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_obs_permission(ctx, "observability.read")
    if denied:
        return denied
    return _ok(await health_monitor.check_all(), ctx)


@require_role(ManagementRole.READ_ONLY)
async def observability_dashboard_handler(_request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_obs_permission(ctx, "observability.read")
    if denied:
        return denied
    return _ok(await all_dashboard_widgets(), ctx)


@require_role(ManagementRole.ADMINISTRATOR)
async def observability_retention_handler(request: web.Request, ctx: ManagementContext) -> web.Response:
    denied = await _check_obs_permission(ctx, "observability.write")
    if denied:
        return denied
    if request.method == "GET":
        return _ok(retention_manager.get_policy().to_dict(), ctx)
    body = await _json_body(request)
    policy = retention_manager.set_policy(
        metrics_days=body.get("metrics_days"),
        logs_days=body.get("logs_days"),
        traces_days=body.get("traces_days"),
        alerts_days=body.get("alerts_days"),
    )
    purged = retention_manager.apply()
    return _ok({"policy": policy.to_dict(), "purged": purged}, ctx)


def register_observability_routes(app: web.Application) -> None:
    prefix = "/management/observability"

    app.router.add_get(prefix, observability_status_handler)
    app.router.add_get(f"{prefix}/metrics", observability_metrics_handler)
    app.router.add_get(f"{prefix}/logs", observability_logs_handler)
    app.router.add_get(f"{prefix}/traces", observability_traces_handler)
    app.router.add_get(f"{prefix}/alerts", observability_alerts_handler)
    app.router.add_post(f"{prefix}/alerts/{{alert_id}}/resolve", observability_alerts_resolve_handler)
    app.router.add_get(f"{prefix}/health", observability_health_handler)
    app.router.add_get(f"{prefix}/dashboard", observability_dashboard_handler)
    app.router.add_get(f"{prefix}/retention", observability_retention_handler)
    app.router.add_put(f"{prefix}/retention", observability_retention_handler)

    logger.info("observability_api_routes_registered prefix=%s", prefix)
