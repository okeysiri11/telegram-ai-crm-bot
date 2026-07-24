"""API handlers — Enterprise Operations Center (Sprint 23.0)."""

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
    return enterprise_hub.operations_center


async def eoc_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "operations_center_ready": health.get("operations_center_ready"),
            "pilot_release_ready": health.get("pilot_release_ready"),
            "tenant_health_ready": health.get("tenant_health_ready"),
            "owner_command_ready": health.get("owner_command_ready"),
            "release_stage": "pilot_release",
            "suite": _suite().status(),
        }
    )


async def eoc_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def eoc_dashboard_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request) if request.method == "POST" else {}
        return json_response(_suite().dashboard(**body))
    except Exception as exc:
        return _handle_error(exc)


async def eoc_tenant_health_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().tenant_health(
                company_id=body.get("company_id", ""),
                dimensions=body.get("dimensions"),
                errors=body.get("errors"),
                warnings=body.get("warnings"),
                performance=float(body.get("performance", 1.0)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def eoc_monitoring_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request) if request.method == "POST" else {}
        return json_response(_suite().platform_monitoring(statuses=body.get("statuses")))
    except Exception as exc:
        return _handle_error(exc)


async def eoc_pilot_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().pilot_profile(
                company_id=body.get("company_id", ""),
                readiness_pct=float(body.get("readiness_pct", 0)),
                staff_trained=bool(body.get("staff_trained", False)),
                daily_users=int(body.get("daily_users", 0)),
                feedback=body.get("feedback"),
                issues=body.get("issues"),
                improvements=body.get("improvements"),
                rollout_status=body.get("rollout_status", "pilot"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def eoc_feedback_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().collect_feedback(
                role=body.get("role", ""),
                message=body.get("message", ""),
                company_id=body.get("company_id", ""),
                kind=body.get("kind", "feedback"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def eoc_usage_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(_suite().usage_analytics(events=body.get("events")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def eoc_advisor_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().daily_ops_report(
                dashboard=body.get("dashboard"),
                pilots=body.get("pilots"),
                usage=body.get("usage"),
                monitoring=body.get("monitoring"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def eoc_release_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().record_release(
                version=body.get("version", ""),
                changelog=body.get("changelog"),
                migrations=body.get("migrations"),
                test_results=body.get("test_results"),
                impact=body.get("impact", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def eoc_incident_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        if body.get("incident_id"):
            return json_response(
                _suite().resolve_incident(
                    incident_id=body["incident_id"],
                    investigation=body.get("investigation", ""),
                    fix=body.get("fix", ""),
                )
            )
        return json_response(
            _suite().open_incident(
                title=body.get("title", ""),
                severity=body.get("severity", "medium"),
                details=body.get("details", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def eoc_owner_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().owner_approve(
                action=body.get("action", ""),
                actor=body.get("actor", ""),
                payload=body.get("payload"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
