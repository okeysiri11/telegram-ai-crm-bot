"""API handlers — Enterprise Command Center Platform (Sprint 26.6)."""

from __future__ import annotations

from aiohttp import web

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.middleware import json_response
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError


def _handle_error(exc: Exception) -> web.Response:
    if isinstance(exc, NotFoundError):
        return json_response({"error": str(exc)}, status=404)
    if isinstance(exc, ValidationError):
        return json_response({"error": str(exc)}, status=400)
    return json_response({"error": str(exc)}, status=500)


def _suite():
    return enterprise_hub.command_center_platform


async def ecc2_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "command_center_ready": health.get("enterprise_command_center_ready"),
            "command_palette_ready": health.get("universal_command_palette_ready"),
            "omnibox_ready": health.get("omnibox_ready"),
            "productivity_hub_ready": health.get("productivity_hub_ready"),
            "ai_command_center_ready": health.get("ai_command_center_ready"),
            "suite": _suite().status(),
        }
    )


async def ecc2_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ecc2_inventory_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().inventory())
    except Exception as exc:
        return _handle_error(exc)


async def ecc2_dashboard_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().dashboard())
    except Exception as exc:
        return _handle_error(exc)


async def ecc2_search_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json() if request.body_exists else {}
    except Exception:
        body = {}
    query = body.get("query") or request.rel_url.query.get("q") or ""
    limit = int(body.get("limit") or request.rel_url.query.get("limit") or 20)
    try:
        return json_response(_suite().search(query, limit=limit, permissions=body.get("permissions")))
    except Exception as exc:
        return _handle_error(exc)


async def ecc2_execute_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
        action = body.get("action") or body.get("command")
        if not action:
            raise ValidationError("action is required")
        return json_response(
            _suite().execute(
                action,
                permissions=body.get("permissions"),
                payload=body.get("payload"),
            )
        )
    except Exception as exc:
        return _handle_error(exc)


async def ecc2_ai_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
        utterance = body.get("utterance") or body.get("text") or body.get("command")
        if not utterance:
            raise ValidationError("utterance is required")
        return json_response(_suite().ai_command(utterance, permissions=body.get("permissions")))
    except Exception as exc:
        return _handle_error(exc)


async def ecc2_suggestions_handler(request: web.Request) -> web.Response:
    try:
        limit = int(request.rel_url.query.get("limit") or 8)
        return json_response(_suite().suggestions(limit=limit))
    except Exception as exc:
        return _handle_error(exc)


async def ecc2_context_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json() if request.body_exists else {}
            return json_response(_suite().context(body))
        return json_response(_suite().context())
    except Exception as exc:
        return _handle_error(exc)


async def ecc2_productivity_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().productivity())
    except Exception as exc:
        return _handle_error(exc)


async def ecc2_analytics_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().analytics())
    except Exception as exc:
        return _handle_error(exc)


async def ecc2_nav_index_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().navigation_index())
    except Exception as exc:
        return _handle_error(exc)


async def ecc2_permissions_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
        action = body.get("action") or "*"
        permissions = body.get("permissions") or []
        return json_response(_suite().validate_permissions(action, permissions))
    except Exception as exc:
        return _handle_error(exc)
