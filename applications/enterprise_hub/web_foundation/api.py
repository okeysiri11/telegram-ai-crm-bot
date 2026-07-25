"""API handlers — Web Foundation (Sprint 26.1)."""

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
    return enterprise_hub.web_foundation


async def ewf_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "web_foundation_ready": health.get("web_foundation_ready"),
            "web_shell_ready": health.get("web_shell_ready"),
            "ui_library_ready": health.get("ui_library_ready"),
            "dashboard_ready": health.get("web_dashboard_ready"),
            "navigation_ready": health.get("navigation_ready"),
            "themes_localization_ready": health.get("themes_localization_ready"),
            "suite": _suite().status(),
        }
    )


async def ewf_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ewf_inventory_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().inventory())
    except Exception as exc:
        return _handle_error(exc)


async def ewf_dashboard_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().dashboard())
    except Exception as exc:
        return _handle_error(exc)
