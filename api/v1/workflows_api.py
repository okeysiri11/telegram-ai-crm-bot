"""Public API v1 — Universal Automation Engine (Epic 45.3)."""

from __future__ import annotations

from typing import Any

from aiohttp import web

from platform_workflows.workflow_manager import workflow_manager


def _owner(request: web.Request, body: dict[str, Any] | None = None) -> str:
    body = body or {}
    return str(
        body.get("owner_id")
        or request.query.get("owner_id")
        or request.headers.get("X-Owner-Id")
        or "anonymous"
    )


def _ok(data: Any, *, status: int = 200) -> web.Response:
    return web.json_response({"success": True, "data": data}, status=status)


def _err(msg: str, *, status: int = 400) -> web.Response:
    return web.json_response({"success": False, "error": msg}, status=status)


async def workflows_list_handler(request: web.Request) -> web.Response:
    return _ok({"status": workflow_manager.status(_owner(request)), "items": workflow_manager.list_workflows(_owner(request))})


async def workflows_history_handler(request: web.Request) -> web.Response:
    return _ok(workflow_manager.history(_owner(request)))


async def workflows_templates_handler(request: web.Request) -> web.Response:
    return _ok(workflow_manager.templates(vertical=request.query.get("vertical")))


async def workflows_jobs_handler(request: web.Request) -> web.Response:
    return _ok(workflow_manager.jobs(_owner(request)))


async def workflows_status_handler(request: web.Request) -> web.Response:
    run_id = request.query.get("run_id")
    if run_id:
        st = workflow_manager.run_status(run_id) or workflow_manager.monitor(run_id)
        if not st:
            return _err("not found", status=404)
        return _ok(st)
    return _ok(workflow_manager.status(_owner(request)))


async def workflows_dashboard_handler(request: web.Request) -> web.Response:
    return _ok(workflow_manager.dashboard(_owner(request)))


async def workflows_run_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except Exception:
        body = {}
    return _ok(
        workflow_manager.run(
            _owner(request, body),
            body.get("workflow_id"),
            goal=body.get("goal"),
            channel=str(body.get("channel") or "api"),
            template_id=body.get("template_id"),
            vertical=str(body.get("vertical") or "company"),
        )
    )


async def workflows_create_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except Exception:
        body = {}
    return _ok(
        workflow_manager.create(
            _owner(request, body),
            goal=body.get("goal"),
            title=body.get("title"),
            blocks=body.get("blocks"),
            template_id=body.get("template_id"),
            vertical=str(body.get("vertical") or "company"),
            channel=str(body.get("channel") or "api"),
        )
    )


async def workflows_clone_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except Exception:
        body = {}
    wid = body.get("workflow_id") or body.get("id")
    if not wid:
        return _err("workflow_id required")
    return _ok(workflow_manager.clone(_owner(request, body), str(wid)))


async def workflows_schedule_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except Exception:
        body = {}
    wid = body.get("workflow_id")
    schedule = body.get("schedule")
    if not wid or not schedule:
        return _err("workflow_id and schedule required")
    return _ok(workflow_manager.schedule(_owner(request, body), str(wid), str(schedule)))


async def workflows_approve_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except Exception:
        body = {}
    run_id = body.get("run_id")
    if not run_id:
        return _err("run_id required")
    return _ok(workflow_manager.approve(_owner(request, body), str(run_id)))


async def workflows_cancel_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except Exception:
        body = {}
    run_id = body.get("run_id")
    if not run_id:
        return _err("run_id required")
    return _ok(workflow_manager.cancel(_owner(request, body), str(run_id)))


async def workflows_remove_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except Exception:
        body = {}
    wid = body.get("workflow_id") or body.get("id") or request.query.get("id")
    if not wid:
        return _err("workflow_id required")
    return _ok(workflow_manager.remove(_owner(request, body), str(wid)))
