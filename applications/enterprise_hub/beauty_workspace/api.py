"""API handlers — Beauty Workspace (Sprint 22.3)."""

from __future__ import annotations

from aiohttp import web

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.middleware import json_response
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError


async def _read_json(request: web.Request) -> dict:
    try:
        data = await request.json()
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _handle_error(exc: Exception) -> web.Response:
    if isinstance(exc, NotFoundError):
        return json_response({"error": str(exc)}, status=404)
    if isinstance(exc, ValidationError):
        return json_response({"error": str(exc)}, status=400)
    return json_response({"error": str(exc)}, status=500)


def _suite():
    return enterprise_hub.beauty_workspace


async def bws_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "beauty_workspace_ready": health.get("beauty_workspace_ready"),
            "reception_desk_ready": health.get("reception_desk_ready"),
            "live_schedule_ready": health.get("live_schedule_ready"),
            "workspace_assistant_ready": health.get("workspace_assistant_ready"),
            "suite": _suite().status(),
        }
    )


async def bws_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def bws_dashboard_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().reception_dashboard())
    except Exception as exc:
        return _handle_error(exc)


async def bws_schedule_handler(request: web.Request) -> web.Response:
    try:
        view = request.rel_url.query.get("view", "day")
        if request.method == "POST":
            body = await _read_json(request)
            view = body.get("view", view)
        return json_response(_suite().schedule(view=view), status=200 if request.method == "GET" else 201)
    except Exception as exc:
        return _handle_error(exc)


async def bws_move_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().move_appointment(
                appointment_id=body.get("appointment_id", ""),
                start=body.get("start"),
                end=body.get("end"),
                employee_id=body.get("employee_id"),
                resource_id=body.get("resource_id"),
            )
        )
    except Exception as exc:
        return _handle_error(exc)


async def bws_panel_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().panel_action(action=body.get("action", ""), payload=body.get("payload")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def bws_quick_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().quick_action(action=body.get("action", ""), payload=body.get("payload")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def bws_search_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request) if request.method == "POST" else {}
        query = body.get("query") or request.rel_url.query.get("query", "")
        return json_response(_suite().search(query=query))
    except Exception as exc:
        return _handle_error(exc)


async def bws_notifications_handler(request: web.Request) -> web.Response:
    try:
        unread = request.rel_url.query.get("unread") == "1"
        return json_response(_suite().notifications(unread_only=unread))
    except Exception as exc:
        return _handle_error(exc)


async def bws_assistant_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().assistant())
    except Exception as exc:
        return _handle_error(exc)
