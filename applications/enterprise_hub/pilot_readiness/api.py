"""API handlers — Pilot Readiness (Sprint 23.1)."""

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
    return enterprise_hub.pilot_readiness


async def epr_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "pilot_ux_ready": health.get("pilot_ux_ready"),
            "workflow_optimized": health.get("workflow_optimized"),
            "empty_states_ready": health.get("empty_states_ready"),
            "pilot_checklist_ready": health.get("pilot_checklist_ready"),
            "suite": _suite().status(),
        }
    )


async def epr_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def epr_ux_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().audit_ux(
                all=bool(body.get("all")),
                surface=body.get("surface", ""),
                metrics=body.get("metrics"),
                metrics_by_surface=body.get("metrics_by_surface"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def epr_workflow_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().optimize_workflows(
                all=bool(body.get("all", True)),
                workflow=body.get("workflow", ""),
                steps=body.get("steps", 5),
                elapsed_ms=body.get("elapsed_ms", 25000),
                profiles=body.get("profiles"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def epr_empty_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(_suite().empty_state(screen=body.get("screen", "")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def epr_first_launch_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().first_launch(user_id=body.get("user_id", ""), role=body.get("role", "admin")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def epr_learning_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().learning_tip(
                user_id=body.get("user_id", ""),
                action=body.get("action", ""),
                repeat_count=int(body.get("repeat_count", 1)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def epr_performance_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(_suite().performance_audit(timings=body.get("timings")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def epr_accessibility_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().accessibility_audit(
                devices=body.get("devices"),
                scale=float(body.get("scale", 1.0)),
                readability=float(body.get("readability", 0.9)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def epr_checklist_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request) if request.method == "POST" else {}
        return json_response(_suite().pilot_checklist(completed=body.get("completed")))
    except Exception as exc:
        return _handle_error(exc)


async def epr_feedback_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().submit_feedback(
                kind=body.get("kind", "idea"),
                message=body.get("message", ""),
                rating=body.get("rating"),
                screenshot=body.get("screenshot"),
                feature=body.get("feature", ""),
                user_id=body.get("user_id", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
