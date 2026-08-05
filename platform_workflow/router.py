"""Workflow Runtime HTTP API — Sprint 36.2.

/api/workflows/*
/api/workflow-runtime/*
/management/v1/workflows/*
"""

from __future__ import annotations

from aiohttp import web

from platform_management.permissions import ManagementRole, require_role
from platform_workflow.service import workflow_runtime_service as wrs


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
async def wf_status_handler(request: web.Request, ctx=None) -> web.Response:
    return web.json_response({"success": True, "data": wrs.status()})


@require_role(ManagementRole.READ_ONLY)
async def wf_list_handler(request: web.Request, ctx=None) -> web.Response:
    data = wrs.list_workflows(
        status=request.query.get("status"),
        published_only=request.query.get("published") == "1",
    )
    return web.json_response({"success": True, "data": {"workflows": data, "count": len(data)}})


@require_role(ManagementRole.READ_ONLY)
async def wf_get_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        data = wrs.get_workflow(request.match_info["id"])
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def wf_create_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    try:
        data = wrs.register(body)
    except ValueError as exc:
        return _error(exc, status=409)
    return web.json_response({"success": True, "data": data}, status=201)


@require_role(ManagementRole.ADMINISTRATOR)
async def wf_update_handler(request: web.Request, ctx=None) -> web.Response:
    body = await request.json()
    try:
        data = wrs.update_workflow(request.match_info["id"], body)
    except (KeyError, ValueError) as exc:
        return _error(exc, status=404 if isinstance(exc, KeyError) else 400)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def wf_publish_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        data = wrs.publish(request.match_info["id"])
    except (KeyError, ValueError) as exc:
        return _error(exc, status=404 if isinstance(exc, KeyError) else 400)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def wf_archive_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        data = wrs.archive(request.match_info["id"])
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.READ_ONLY)
async def wf_versions_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        data = wrs.versions(request.match_info["id"])
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": {"versions": data}})


@require_role(ManagementRole.ADMINISTRATOR)
async def wf_execute_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        body = await request.json()
    except Exception:
        body = {}
    try:
        data = await wrs.execute(request.match_info["id"], body)
    except (KeyError, ValueError) as exc:
        return _error(exc, status=404 if isinstance(exc, KeyError) else 400)
    except Exception as exc:
        return _error(exc, status=500)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.READ_ONLY)
async def wf_runs_handler(request: web.Request, ctx=None) -> web.Response:
    data = wrs.list_runs(workflow_id=request.query.get("workflow_id"))
    return web.json_response({"success": True, "data": {"runs": data, "count": len(data)}})


@require_role(ManagementRole.READ_ONLY)
async def wf_run_get_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        data = wrs.get_run(request.match_info["run_id"])
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def wf_cancel_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        data = await wrs.cancel(request.match_info["run_id"])
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def wf_retry_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        data = await wrs.retry(request.match_info["run_id"], actor=_actor(request))
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def wf_rollback_handler(request: web.Request, ctx=None) -> web.Response:
    try:
        data = await wrs.rollback(request.match_info["run_id"], actor=_actor(request))
    except KeyError as exc:
        return _error(exc, status=404)
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def wf_scheduler_tick_handler(request: web.Request, ctx=None) -> web.Response:
    data = await wrs.process_scheduled()
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.READ_ONLY)
async def wf_monitoring_handler(request: web.Request, ctx=None) -> web.Response:
    return web.json_response({"success": True, "data": wrs.monitoring()})


WORKFLOW_ROUTE_SPECS: list[tuple[str, str, object]] = [
    ("GET", "", wf_status_handler),
    ("GET", "workflows", wf_list_handler),
    ("GET", "workflows/{id}", wf_get_handler),
    ("POST", "workflows", wf_create_handler),
    ("PUT", "workflows/{id}", wf_update_handler),
    ("POST", "workflows/{id}/publish", wf_publish_handler),
    ("POST", "workflows/{id}/archive", wf_archive_handler),
    ("GET", "workflows/{id}/versions", wf_versions_handler),
    ("POST", "workflows/{id}/execute", wf_execute_handler),
    ("GET", "runs", wf_runs_handler),
    ("GET", "runs/{run_id}", wf_run_get_handler),
    ("POST", "runs/{run_id}/cancel", wf_cancel_handler),
    ("POST", "runs/{run_id}/retry", wf_retry_handler),
    ("POST", "runs/{run_id}/rollback", wf_rollback_handler),
    ("POST", "scheduler/tick", wf_scheduler_tick_handler),
    ("GET", "monitoring", wf_monitoring_handler),
]


def _mount(app: web.Application, prefix: str, specs: list[tuple[str, str, object]]) -> None:
    for method, rel, handler in specs:
        rel = rel.strip("/")
        path = f"{prefix}/{rel}" if rel else prefix
        getattr(app.router, f"add_{method.lower()}")(path, handler)


def register_workflow_runtime_routes(app: web.Application) -> None:
    from platform_api.versioning import MANAGEMENT_V1_PREFIX, register_dual_prefix_routes

    register_dual_prefix_routes(
        app,
        route_specs=WORKFLOW_ROUTE_SPECS,  # type: ignore[arg-type]
        v1_prefix=f"{MANAGEMENT_V1_PREFIX}/workflows",
        legacy_prefix="/management/workflows",
    )
    _mount(app, "/api/workflows", WORKFLOW_ROUTE_SPECS)
    _mount(app, "/api/workflow-runtime", WORKFLOW_ROUTE_SPECS)
