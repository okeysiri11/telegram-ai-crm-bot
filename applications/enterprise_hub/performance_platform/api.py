"""API handlers — Enterprise Performance Platform (Sprint 21.7)."""

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
    return enterprise_hub.performance_platform


async def epf_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "performance_platform_ready": health.get("performance_platform_ready"),
            "load_testing_ready": health.get("load_testing_ready"),
            "autoscaling_ready": health.get("autoscaling_ready"),
            "performance_certification_ready": health.get("performance_certification_ready"),
            "suite": _suite().status(),
        }
    )


async def epf_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def epf_profile_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request) if request.method == "POST" else {}
        target = body.get("target") or request.rel_url.query.get("target")
        return json_response(_suite().profile(target or None), status=201 if request.method == "POST" else 200)
    except Exception as exc:
        return _handle_error(exc)


async def epf_benchmark_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().benchmark(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def epf_load_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().load_test(concurrent_users=int(body.get("concurrent_users", 500) or 500)),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def epf_stress_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().stress_test(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def epf_cache_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().cache_put(
                key=body.get("key", ""),
                value=body.get("value"),
                ttl=float(body.get("ttl", 60) or 60),
                backend=body.get("backend", "redis"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def epf_dashboard_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().dashboard())
    except Exception as exc:
        return _handle_error(exc)


async def epf_certify_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().certify(), status=201)
    except Exception as exc:
        return _handle_error(exc)
