"""API handlers — Chaos Engineering (Sprint 25.3)."""

from __future__ import annotations

import uuid

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
    return enterprise_hub.chaos_engineering


async def ece_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "chaos_engineering_ready": health.get("chaos_engineering_ready"),
            "failure_injection_ready": health.get("failure_injection_ready"),
            "recovery_engine_ready": health.get("recovery_engine_ready"),
            "circuit_breaker_ready": health.get("circuit_breaker_ready"),
            "suite": _suite().status(),
        }
    )


async def ece_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ece_scenario_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().create_scenario(
                scenario_id=body.get("scenario_id") or f"chs_{uuid.uuid4().hex[:8]}",
                name=body.get("name", ""),
                description=body.get("description", ""),
                target_service=body.get("target_service", ""),
                failure_type=body.get("failure_type", ""),
                duration_sec=int(body.get("duration_sec", 30)),
                recovery_policy=body.get("recovery_policy", "auto"),
                expected_result=body.get("expected_result", "service_recovers"),
                validation_rules=body.get("validation_rules"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ece_scenarios_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().list_scenarios())
    except Exception as exc:
        return _handle_error(exc)


async def ece_run_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().run_scenario(
                scenario_id=body.get("scenario_id", ""),
                retry_strategy=body.get("retry_strategy", "exponential_backoff"),
                fallback=body.get("fallback", "degraded_mode"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ece_circuit_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().circuit_check(
                failure_count=int(body.get("failure_count", 0)),
                success_after_open=int(body.get("success_after_open", 0)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ece_retry_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().retry_check(
                strategy=body.get("strategy", "exponential_backoff"),
                max_attempts=int(body.get("max_attempts", 3)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ece_fallback_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().fallback_check(preferred=body.get("preferred", "degraded_mode")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ece_health_monitor_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().health_monitor(services=body.get("services"), incidents=body.get("incidents")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ece_dependencies_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(_suite().dependency_map(failed_service=body.get("failed_service")))
    except Exception as exc:
        return _handle_error(exc)


async def ece_incidents_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().list_incidents())
    except Exception as exc:
        return _handle_error(exc)


async def ece_dashboard_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().dashboard())
    except Exception as exc:
        return _handle_error(exc)
