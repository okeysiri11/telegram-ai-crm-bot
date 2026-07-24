"""API handlers — Enterprise Command Center (Sprint 20.12)."""

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
    return enterprise_hub.command_center


async def ecc_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "command_center_ready": health.get("command_center_ready"),
            "executive_dashboard_ready": health.get("executive_dashboard_ready"),
            "health_monitor_ready": health.get("health_monitor_ready"),
            "action_center_ready": health.get("action_center_ready"),
            "suite": _suite().status(),
        }
    )


async def ecc_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ecc_dashboards_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        if request.method == "GET":
            return json_response({**suite.dashboards.status(), "items": suite.dashboards.list_all()})
        body = await _read_json(request)
        created = suite.dashboards.create(
            kind=body.get("kind", "custom"),
            title=body.get("title", ""),
            workspace_id=body.get("workspace_id"),
        )
        return json_response(created, status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ecc_executive_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request) if request.method == "POST" else {}
        return json_response(
            _suite().executive.render(
                health_score=float(body.get("health_score", 0.82) or 0.82),
                workspace_id=body.get("workspace_id"),
            )
        )
    except Exception as exc:
        return _handle_error(exc)


async def ecc_enterprise_health_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request) if request.method == "POST" else {}
        scores = body.get("scores") if isinstance(body.get("scores"), dict) else None
        return json_response(_suite().health.evaluate(scores=scores), status=201 if request.method == "POST" else 200)
    except Exception as exc:
        return _handle_error(exc)


async def ecc_situation_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().situation.brief(), status=201 if request.method == "POST" else 200)
    except Exception as exc:
        return _handle_error(exc)


async def ecc_assistant_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(_suite().assistant.assist(prompt=body.get("prompt", "daily report")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ecc_alerts_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        if request.method == "GET":
            return json_response({**suite.alerts.status(), "items": suite.alerts.list_open()})
        body = await _read_json(request)
        return json_response(
            suite.alerts.raise_alert(
                kind=body.get("kind", "critical_event"),
                severity=body.get("severity", "warning"),
                message=body.get("message", ""),
                source=body.get("source", "command_center"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ecc_actions_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        if request.method == "GET":
            return json_response({**suite.actions.status(), "items": suite.actions.list_all()})
        body = await _read_json(request)
        return json_response(
            suite.actions.dispatch(
                kind=body.get("kind", "assign_task"),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else None,
                actor=body.get("actor", "executive"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ecc_command_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().dispatcher.dispatch_command(
                command=body.get("command", ""),
                actor=body.get("actor", "executive"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ecc_realtime_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().realtime.snapshot())
    except Exception as exc:
        return _handle_error(exc)


async def ecc_map_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().enterprise_map.render())
    except Exception as exc:
        return _handle_error(exc)


async def ecc_analytics_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        return json_response(
            {
                "executive_metrics": suite.executive_metrics.report(),
                "realtime": suite.realtime_analytics.report(),
                "trends": suite.trends.report(),
            }
        )
    except Exception as exc:
        return _handle_error(exc)
