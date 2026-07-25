"""API handlers — Production Readiness (Sprint 25.6)."""

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
    return enterprise_hub.production_readiness


async def epd_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "production_platform_ready": health.get("production_platform_ready"),
            "continuous_health_ready": health.get("continuous_health_ready"),
            "centralized_logging_ready": health.get("centralized_logging_ready"),
            "production_scaling_ready": health.get("production_scaling_ready"),
            "suite": _suite().status(),
        }
    )


async def epd_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def epd_gate_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().run_gate(
                release=body.get("release"),
                failed_health=body.get("failed_health"),
                active_alerts=body.get("active_alerts"),
                failed_deployment=body.get("failed_deployment"),
                monitoring_overrides=body.get("monitoring_overrides"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def epd_dashboard_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().dashboard())
    except Exception as exc:
        return _handle_error(exc)
