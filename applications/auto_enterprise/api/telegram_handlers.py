"""HTTP handlers — Auto Ops Telegram staff channel (AUTO 1.4)."""

from __future__ import annotations

from aiohttp import web

from applications.auto_enterprise.api.middleware import json_response
from applications.auto_enterprise.api.ops_handlers import _actor, _org, _read_json, _role, _status
from services.auto_ops import get_auto_ops_service


async def telegram_status_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    result = await svc.telegram_bot_status(_org(request), _role(request))
    return json_response(result, status=_status(result))


async def telegram_members_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request) if request.method == "POST" else {}
    org = _org(request, body)
    actor_role = _role(request)
    if request.method == "GET":
        result = await svc.list_telegram_members(org, actor_role)
        return json_response(result, status=_status(result))
    result = await svc.upsert_telegram_member(org, body, actor_role, _actor(request))
    return json_response(result, status=_status(result, created=True))


async def telegram_inbound_handler(request: web.Request) -> web.Response:
    """Test/ops inbound without calling Telegram HTTP API."""
    svc = get_auto_ops_service()
    body = await _read_json(request)
    try:
        tid = int(body.get("telegram_id"))
    except (TypeError, ValueError):
        return json_response({"ok": False, "error": "validation", "message_ru": "Укажите telegram_id"}, status=400)
    result = await svc.handle_telegram_inbound(
        telegram_id=tid,
        text=str(body.get("text") or ""),
        extra=body.get("extra") if isinstance(body.get("extra"), dict) else {},
        callback_data=body.get("callback_data"),
    )
    return json_response(result, status=_status(result))


async def telegram_summary_handler(request: web.Request) -> web.Response:
    svc = get_auto_ops_service()
    body = await _read_json(request)
    kind = request.match_info.get("kind") or body.get("kind") or "morning"
    role = _role(request, body)
    from services.auto_ops.rbac import require

    denied = require(role, "admin")
    if denied:
        return json_response(denied, status=_status(denied))
    result = await svc.send_telegram_summary(str(kind), _org(request, body))
    return json_response(result, status=_status(result))
