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


async def _resolve_server_side_scope(
    ctx: Any,
) -> tuple[str | None, str | None, str | None, str | None]:
    """Sprint 47.0 (CC-3): resolve the caller's real active_vertical/active_persona/
    authenticated_role/tenant_id from server-side state (the same
    vertical_role_registry the Telegram bot uses, plus TenantContextService), instead
    of trusting whatever the client claims in the request body. Returns
    (active_vertical, active_persona, authenticated_role, tenant_id) — any of which
    may be None if there is no authenticated Telegram identity to resolve a session
    for (e.g. a pure API-key caller with no bot-side session)."""
    telegram_id = getattr(ctx, "actor_telegram_id", None)
    if not telegram_id:
        return None, None, None, None

    active_vertical: str | None = None
    active_persona: str | None = None
    authenticated_role: str | None = None
    tenant_id: str | None = None

    try:
        from services.vertical_role_registry import vertical_role_registry

        sess = vertical_role_registry.get(int(telegram_id))
        active_vertical = sess.active_vertical
        active_persona = sess.active_persona
        authenticated_role = sess.authenticated_role
    except Exception:  # noqa: BLE001
        logger.exception("ai_command_vertical_session_resolve_failed telegram_id=%s", telegram_id)

    try:
        from services.tenant_context import TenantContextService

        tenant_ctx = await TenantContextService.resolve_for_user(int(telegram_id))
        if tenant_ctx is not None:
            tenant_id = str(tenant_ctx.tenant_id)
    except Exception:  # noqa: BLE001
        logger.exception("ai_command_tenant_resolve_failed telegram_id=%s", telegram_id)

    return active_vertical, active_persona, authenticated_role, tenant_id


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

    active_vertical, active_persona, authenticated_role, tenant_id = await _resolve_server_side_scope(ctx)

    result = await ai_command_center.handle(
        text,
        owner_id=owner,
        channel=str(body.get("channel") or "api"),
        session_id=body.get("session_id"),
        # authenticated_role (server-resolved) takes precedence over the client-
        # declared body.role for tool-availability filtering; only fall back to the
        # client value when there is no server-side session to resolve one from.
        role=authenticated_role or str(body.get("role") or "owner"),
        voice=bool(body.get("voice")),
        max_steps=body.get("max_steps"),
        active_vertical=active_vertical,
        active_persona=active_persona,
        authenticated_role=authenticated_role,
        tenant_id=tenant_id,
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
