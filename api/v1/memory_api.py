"""Public API v1 — Continuous Memory (Epic 45.2).

GET  /api/v1/memory
GET  /api/v1/memory/search
GET  /api/v1/memory/context
GET  /api/v1/memory/timeline
GET  /api/v1/memory/resume
POST /api/v1/memory/save
POST /api/v1/memory/summary
POST /api/v1/memory/project
POST /api/v1/memory/pin
DELETE /api/v1/memory/remove
"""

from __future__ import annotations

from typing import Any

from aiohttp import web

from platform_memory.memory_manager import memory_manager


def _owner(request: web.Request, body: dict[str, Any] | None = None) -> str:
    body = body or {}
    return str(
        body.get("owner_id")
        or request.query.get("owner_id")
        or request.headers.get("X-Owner-Id")
        or "anonymous"
    )


def _company(request: web.Request, body: dict[str, Any] | None = None) -> str:
    body = body or {}
    return str(body.get("company_id") or request.query.get("company_id") or "default")


def _ok(data: Any, *, status: int = 200) -> web.Response:
    return web.json_response({"success": True, "data": data}, status=status)


def _err(msg: str, *, status: int = 400) -> web.Response:
    return web.json_response({"success": False, "error": msg}, status=status)


async def memory_get_handler(request: web.Request) -> web.Response:
    return _ok(memory_manager.status(_owner(request), company_id=_company(request)))


async def memory_search_handler(request: web.Request) -> web.Response:
    q = request.query.get("q") or request.query.get("query") or ""
    return _ok(memory_manager.search(_owner(request), q, company_id=_company(request)))


async def memory_context_handler(request: web.Request) -> web.Response:
    prompt = request.query.get("prompt") or ""
    return _ok(
        memory_manager.context(
            _owner(request),
            prompt,
            company_id=_company(request),
            channel=request.query.get("channel") or "api",
            project_id=request.query.get("project_id"),
        )
    )


async def memory_timeline_handler(request: web.Request) -> web.Response:
    window = request.query.get("window") or "today"
    return _ok(memory_manager.timeline(_owner(request), window=window, company_id=_company(request)))


async def memory_resume_handler(request: web.Request) -> web.Response:
    return _ok(
        memory_manager.resume(
            _owner(request),
            company_id=_company(request),
            channel=request.query.get("channel") or "api",
        )
    )


async def memory_workspace_handler(request: web.Request) -> web.Response:
    return _ok(memory_manager.workspace(_owner(request), company_id=_company(request)))


async def memory_save_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except Exception:
        body = {}
    title = body.get("title")
    content = body.get("content")
    if not title:
        return _err("title required")
    return _ok(
        memory_manager.save(
            _owner(request, body),
            title=str(title),
            content=str(content or title),
            level=str(body.get("level") or "working"),
            kind=str(body.get("kind") or "note"),
            channel=str(body.get("channel") or "api"),
            project_id=body.get("project_id"),
            company_id=_company(request, body),
            tags=body.get("tags"),
            metadata=body.get("metadata"),
        )
    )


async def memory_summary_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except Exception:
        body = {}
    return _ok(
        memory_manager.summary(
            _owner(request, body),
            company_id=_company(request, body),
            session_id=body.get("session_id"),
            channel=str(body.get("channel") or "api"),
        )
    )


async def memory_project_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except Exception:
        body = {}
    project_id = body.get("project_id") or body.get("id")
    title = body.get("title")
    if not project_id or not title:
        return _err("project_id and title required")
    return _ok(
        memory_manager.project(
            _owner(request, body),
            str(project_id),
            str(title),
            company_id=_company(request, body),
            content=body.get("content", ""),
            channel=str(body.get("channel") or "api"),
            status=str(body.get("status") or "active"),
        )
    )


async def memory_pin_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except Exception:
        body = {}
    mid = body.get("memory_id") or body.get("id")
    if not mid:
        return _err("memory_id required")
    pinned = memory_manager.pin(_owner(request, body), str(mid), company_id=_company(request, body))
    if not pinned:
        return _err("not found", status=404)
    return _ok(pinned)


async def memory_remove_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except Exception:
        body = {}
    mid = body.get("memory_id") or body.get("id") or request.query.get("id")
    if not mid:
        return _err("memory_id required")
    ok = memory_manager.remove(
        _owner(request, body),
        str(mid),
        company_id=_company(request, body),
        role=str(body.get("role") or "owner"),
    )
    if not ok:
        return _err("not found or forbidden", status=404)
    return _ok({"removed": True, "id": mid})
