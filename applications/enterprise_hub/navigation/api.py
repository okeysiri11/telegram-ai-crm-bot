"""API handlers — Enterprise Navigation (Sprint 26.7)."""

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
    return enterprise_hub.enterprise_navigation


async def env_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "navigation_ready": health.get("enterprise_navigation_ready", health.get("navigation_platform_ready")),
            "workspace_federation_ready": health.get("workspace_federation_ready"),
            "global_search_ready": health.get("global_search_ready"),
            "application_registry_ready": health.get("application_registry_ready"),
            "suite": _suite().status(),
        }
    )


async def env_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def env_inventory_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().inventory())
    except Exception as exc:
        return _handle_error(exc)


async def env_dashboard_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().dashboard())
    except Exception as exc:
        return _handle_error(exc)


async def env_global_nav_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().global_navigation())
    except Exception as exc:
        return _handle_error(exc)


async def env_workspaces_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().workspaces())
    except Exception as exc:
        return _handle_error(exc)


async def env_switch_workspace_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
        kind = body.get("workspace") or body.get("kind") or body.get("id")
        if not kind:
            raise ValidationError("workspace is required")
        return json_response(_suite().switch_workspace(kind, permissions=body.get("permissions")))
    except Exception as exc:
        return _handle_error(exc)


async def env_registry_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().application_registry())
    except Exception as exc:
        return _handle_error(exc)


async def env_search_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json() if request.body_exists else {}
    except Exception:
        body = {}
    query = body.get("query") or request.rel_url.query.get("q") or ""
    limit = int(body.get("limit") or request.rel_url.query.get("limit") or 20)
    try:
        return json_response(_suite().search(query, limit=limit, permissions=body.get("permissions")))
    except Exception as exc:
        return _handle_error(exc)


async def env_favorites_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(_suite().add_favorite(body))
        return json_response(_suite().favorites())
    except Exception as exc:
        return _handle_error(exc)


async def env_history_handler(request: web.Request) -> web.Response:
    try:
        kind = request.rel_url.query.get("kind")
        return json_response(_suite().history(kind))
    except Exception as exc:
        return _handle_error(exc)


async def env_breadcrumbs_handler(request: web.Request) -> web.Response:
    try:
        path = request.rel_url.query.get("path") or "/workspace"
        return json_response(_suite().breadcrumbs(path))
    except Exception as exc:
        return _handle_error(exc)


async def env_quick_switch_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json() if request.body_exists else {}
    except Exception:
        body = {}
    try:
        return json_response(
            _suite().quick_switcher(step=int(body.get("step") or 1), target=body.get("target"))
        )
    except Exception as exc:
        return _handle_error(exc)


async def env_analytics_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().analytics())
    except Exception as exc:
        return _handle_error(exc)


async def env_permissions_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
        return json_response(
            _suite().validate_permissions(body.get("resource") or "navigate", body.get("permissions") or [])
        )
    except Exception as exc:
        return _handle_error(exc)
