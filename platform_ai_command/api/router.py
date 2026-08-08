"""AI Command Center HTTP API — /management/v1/ai-command · /api/ai-command."""

from __future__ import annotations

import logging
from typing import Any

from aiohttp import web

from platform_ai_command.core.command_center import ai_command_center
from platform_management.permissions import ManagementRole, require_role

logger = logging.getLogger(__name__)


def _ok(data: Any, *, status: int = 200) -> web.Response:
    return web.json_response({"success": True, "data": data}, status=status)


def _err(msg: str, *, status: int = 400) -> web.Response:
    return web.json_response({"success": False, "error": msg}, status=status)


@require_role(ManagementRole.READ_ONLY)
async def cmd_home(request: web.Request, ctx=None) -> web.Response:
    owner = str(getattr(ctx, "actor_telegram_id", None) or request.query.get("owner_id") or "web")
    return _ok(ai_command_center.home(owner))


@require_role(ManagementRole.READ_ONLY)
async def cmd_tools(request: web.Request, ctx=None) -> web.Response:
    from platform_ai_command.tools.catalog import list_tools

    return _ok({"tools": [{"id": t.id, "name_ru": t.name_ru, "category": t.category} for t in list_tools()]})


@require_role(ManagementRole.READ_ONLY)
async def cmd_history(request: web.Request, ctx=None) -> web.Response:
    from platform_ai_command.history.store import command_history

    owner = str(getattr(ctx, "actor_telegram_id", None) or request.query.get("owner_id") or "web")
    return _ok({"history": command_history.list(owner)})


@require_role(ManagementRole.ADMINISTRATOR)
async def cmd_chat(request: web.Request, ctx=None) -> web.Response:
    try:
        body = await request.json()
    except Exception:
        body = {}
    text = str(body.get("text") or body.get("message") or "").strip()
    if not text:
        return _err("text required")
    owner = str(body.get("owner_id") or getattr(ctx, "actor_telegram_id", None) or "api")
    result = await ai_command_center.handle(
        text,
        owner_id=owner,
        channel=str(body.get("channel") or "api"),
        session_id=body.get("session_id"),
        role=str(body.get("role") or "owner"),
        voice=bool(body.get("voice")),
        max_steps=body.get("max_steps"),
    )
    return _ok(result, status=201)


@require_role(ManagementRole.ADMINISTRATOR)
async def cmd_retry(request: web.Request, ctx=None) -> web.Response:
    plan_id = request.match_info["plan_id"]
    owner = str(getattr(ctx, "actor_telegram_id", None) or request.query.get("owner_id") or "api")
    return _ok(await ai_command_center.retry(owner, plan_id))


@require_role(ManagementRole.ADMINISTRATOR)
async def cmd_new_dialog(request: web.Request, ctx=None) -> web.Response:
    try:
        body = await request.json()
    except Exception:
        body = {}
    owner = str(body.get("owner_id") or getattr(ctx, "actor_telegram_id", None) or "api")
    key = ai_command_center.new_dialog(owner, body.get("session_id"))
    return _ok({"session_key": key})


ROUTE_SPECS = [
    ("GET", "home", cmd_home),
    ("GET", "tools", cmd_tools),
    ("GET", "history", cmd_history),
    ("POST", "chat", cmd_chat),
    ("POST", "dialog", cmd_new_dialog),
    ("POST", "retry/{plan_id}", cmd_retry),
]


def register_ai_command_routes(app: web.Application) -> None:
    from platform_api.versioning import MANAGEMENT_V1_PREFIX, register_dual_prefix_routes

    register_dual_prefix_routes(
        app,
        route_specs=ROUTE_SPECS,  # type: ignore[arg-type]
        v1_prefix=f"{MANAGEMENT_V1_PREFIX}/ai-command",
        legacy_prefix="/management/ai-command",
    )
    for method, path, handler in ROUTE_SPECS:
        full = f"/api/ai-command/{path}"
        if method == "GET":
            app.router.add_get(full, handler)
        else:
            app.router.add_post(full, handler)
    logger.info("ai_command_routes_registered")
