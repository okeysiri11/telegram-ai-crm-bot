"""Public API v1 — Dual Experience mode endpoints (Epic 45.1).

GET  /api/v1/mode
POST /api/v1/mode/change
POST /api/v1/mode/voice
GET  /api/v1/mode/status
"""

from __future__ import annotations

from typing import Any

from aiohttp import web

from platform_modes.manager import mode_manager


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


async def mode_get_handler(request: web.Request) -> web.Response:
    return _ok(mode_manager.status(_owner(request)))


async def mode_status_handler(request: web.Request) -> web.Response:
    return _ok(mode_manager.status(_owner(request)))


async def mode_change_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except Exception:
        body = {}
    mode = body.get("mode")
    if not mode:
        return _err("mode required")
    return _ok(mode_manager.change(_owner(request, body), mode, channel=str(body.get("channel") or "api")))


async def mode_voice_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except Exception:
        body = {}
    enabled = body.get("enabled")
    if enabled is None:
        enabled = body.get("voice", True)
    return _ok(
        mode_manager.set_voice(
            _owner(request, body),
            bool(enabled),
            channel=str(body.get("channel") or "api"),
        )
    )


async def mode_settings_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except Exception:
        body = {}
    return _ok(mode_manager.update_settings(_owner(request, body), body))


async def mode_remember_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except Exception:
        body = {}
    return _ok(mode_manager.remember_default(_owner(request, body), body.get("mode")))
