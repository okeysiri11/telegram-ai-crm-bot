"""API handlers — Design System (Sprint 26.2)."""

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
    return enterprise_hub.design_system


async def eds_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "design_system_ready": health.get("design_system_ready"),
            "tokens_ready": health.get("design_tokens_ready"),
            "component_catalog_ready": health.get("component_catalog_ready"),
            "adaptive_grid_ready": health.get("adaptive_grid_ready"),
            "accessibility_ready": health.get("accessibility_ready"),
            "themes_ready": health.get("design_themes_ready"),
            "documentation_ready": health.get("design_documentation_ready"),
            "suite": _suite().status(),
        }
    )


async def eds_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def eds_inventory_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().inventory())
    except Exception as exc:
        return _handle_error(exc)


async def eds_documentation_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().documentation())
    except Exception as exc:
        return _handle_error(exc)


async def eds_dashboard_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().dashboard())
    except Exception as exc:
        return _handle_error(exc)
