"""Hercules Management + Public API.

/management/v1/hercules/*
/api/hercules/*
"""

from __future__ import annotations

import logging
from typing import Any

from aiohttp import web

from platform_hercules.core.models import ExecutionContext
from platform_hercules.runtime.hercules_runtime import hercules_runtime
from platform_management.permissions import ManagementRole, require_role

logger = logging.getLogger(__name__)


def _ok(data: Any, *, status: int = 200) -> web.Response:
    return web.json_response({"success": True, "data": data}, status=status)


def _err(msg: str, *, status: int = 400) -> web.Response:
    return web.json_response({"success": False, "error": msg}, status=status)


@require_role(ManagementRole.READ_ONLY)
async def hercules_status(request: web.Request, ctx=None) -> web.Response:
    return _ok({"version": hercules_runtime.VERSION, "health": hercules_runtime.dashboard()["health"]})


@require_role(ManagementRole.READ_ONLY)
async def hercules_dashboard(request: web.Request, ctx=None) -> web.Response:
    return _ok(hercules_runtime.dashboard())


@require_role(ManagementRole.READ_ONLY)
async def hercules_metrics(request: web.Request, ctx=None) -> web.Response:
    return _ok(hercules_runtime.dashboard()["metrics"])


@require_role(ManagementRole.READ_ONLY)
async def hercules_resources(request: web.Request, ctx=None) -> web.Response:
    d = hercules_runtime.dashboard()
    return _ok({"resources": d["resources"], "gpu": d["gpu"], "cpu": d["cpu"]})


@require_role(ManagementRole.READ_ONLY)
async def hercules_queues(request: web.Request, ctx=None) -> web.Response:
    return _ok(hercules_runtime.dashboard()["queues"])


@require_role(ManagementRole.READ_ONLY)
async def hercules_workers(request: web.Request, ctx=None) -> web.Response:
    return _ok({"workers": hercules_runtime.dashboard()["workers"]})


@require_role(ManagementRole.READ_ONLY)
async def hercules_runtime_view(request: web.Request, ctx=None) -> web.Response:
    return _ok(
        {
            "domains": hercules_runtime.dashboard()["domains"],
            "jobs": hercules_runtime.dashboard()["jobs"],
        }
    )


@require_role(ManagementRole.READ_ONLY)
async def hercules_telemetry(request: web.Request, ctx=None) -> web.Response:
    from platform_hercules.telemetry.telemetry import hercules_telemetry

    return _ok(hercules_telemetry.diagnostics())


@require_role(ManagementRole.READ_ONLY)
async def hercules_jobs_list(request: web.Request, ctx=None) -> web.Response:
    return _ok({"jobs": hercules_runtime.dashboard()["jobs"]})


@require_role(ManagementRole.READ_ONLY)
async def hercules_job_status(request: web.Request, ctx=None) -> web.Response:
    job_id = request.match_info["job_id"]
    st = hercules_runtime.status(job_id)
    if not st:
        return _err("job not found", status=404)
    return _ok(st)


@require_role(ManagementRole.ADMINISTRATOR)
async def hercules_submit(request: web.Request, ctx=None) -> web.Response:
    try:
        body = await request.json()
    except Exception:
        body = {}
    prompt = str(body.get("prompt") or "")
    if not prompt:
        return _err("prompt required")
    owner = str(body.get("owner_id") or getattr(ctx, "actor_telegram_id", None) or "api")
    job = await hercules_runtime.submit_ai(
        ExecutionContext(
            owner_id=owner,
            channel="api",
            vertical=body.get("vertical"),
            priority=int(body.get("priority") or 5),
        ),
        prompt=prompt,
        modality=str(body.get("modality") or "text"),
        vertical=body.get("vertical"),
    )
    return _ok(hercules_runtime.status(job.id), status=201)


@require_role(ManagementRole.ADMINISTRATOR)
async def hercules_cancel(request: web.Request, ctx=None) -> web.Response:
    job_id = request.match_info["job_id"]
    st = hercules_runtime.cancel(job_id)
    if not st:
        return _err("job not found", status=404)
    return _ok(st)


@require_role(ManagementRole.ADMINISTRATOR)
async def hercules_retry(request: web.Request, ctx=None) -> web.Response:
    job_id = request.match_info["job_id"]
    try:
        job = await hercules_runtime.retry(job_id)
    except KeyError:
        return _err("job not found", status=404)
    return _ok(hercules_runtime.status(job.id))


HERCULES_ROUTE_SPECS = [
    ("GET", "status", hercules_status),
    ("GET", "dashboard", hercules_dashboard),
    ("GET", "metrics", hercules_metrics),
    ("GET", "resources", hercules_resources),
    ("GET", "queues", hercules_queues),
    ("GET", "workers", hercules_workers),
    ("GET", "runtime", hercules_runtime_view),
    ("GET", "telemetry", hercules_telemetry),
    ("GET", "jobs", hercules_jobs_list),
    ("GET", "jobs/{job_id}", hercules_job_status),
    ("POST", "jobs", hercules_submit),
    ("POST", "jobs/{job_id}/cancel", hercules_cancel),
    ("POST", "jobs/{job_id}/retry", hercules_retry),
]


def register_hercules_routes(app: web.Application) -> None:
    from platform_api.versioning import MANAGEMENT_V1_PREFIX, register_dual_prefix_routes

    register_dual_prefix_routes(
        app,
        route_specs=HERCULES_ROUTE_SPECS,  # type: ignore[arg-type]
        v1_prefix=f"{MANAGEMENT_V1_PREFIX}/hercules",
        legacy_prefix="/management/hercules",
    )
    # Public additive /api/hercules (same handlers)
    for method, path, handler in HERCULES_ROUTE_SPECS:
        full = f"/api/hercules/{path}" if path else "/api/hercules"
        if method == "GET":
            app.router.add_get(full, handler)
        elif method == "POST":
            app.router.add_post(full, handler)
    logger.info("hercules_api_routes_registered v1=%s/hercules", MANAGEMENT_V1_PREFIX)
