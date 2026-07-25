"""API handlers — Release Candidate (Sprint 26.8)."""

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
    return enterprise_hub.release_candidate


async def rc_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "release_candidate_ready": health.get("release_candidate_ready"),
            "platform_integrated": health.get("platform_integrated"),
            "suite": _suite().status(),
        }
    )


async def rc_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def rc_inventory_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().inventory())
    except Exception as exc:
        return _handle_error(exc)


async def rc_dashboard_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().dashboard())
    except Exception as exc:
        return _handle_error(exc)


async def rc_health_report_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().health_report())
    except Exception as exc:
        return _handle_error(exc)


async def rc_integration_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().integration())
    except Exception as exc:
        return _handle_error(exc)


async def rc_registry_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().registry())
    except Exception as exc:
        return _handle_error(exc)


async def rc_routes_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().routes())
    except Exception as exc:
        return _handle_error(exc)


async def rc_security_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().security())
    except Exception as exc:
        return _handle_error(exc)


async def rc_performance_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().performance())
    except Exception as exc:
        return _handle_error(exc)


async def rc_documentation_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().documentation())
    except Exception as exc:
        return _handle_error(exc)
