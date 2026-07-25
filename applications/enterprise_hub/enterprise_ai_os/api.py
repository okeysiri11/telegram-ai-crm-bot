"""API handlers — Enterprise Multi-Agent OS (Sprint 27.1)."""

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
    return enterprise_hub.enterprise_ai_os


async def maos_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "enterprise_ai_os_ready": health.get("enterprise_ai_os_ready"),
            "executive_ai_ready": health.get("executive_ai_ready"),
            "agent_registry_ready": health.get("agent_registry_v2_ready"),
            "suite": _suite().status(),
        }
    )


async def maos_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def maos_inventory_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().inventory())
    except Exception as exc:
        return _handle_error(exc)


async def maos_dashboard_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().dashboard())
    except Exception as exc:
        return _handle_error(exc)


async def maos_executive_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
        goal = body.get("goal") or body.get("task")
        if not goal:
            raise ValidationError("goal is required")
        return json_response(_suite().executive(goal, priority=int(body.get("priority") or 5)))
    except Exception as exc:
        return _handle_error(exc)


async def maos_agents_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().agents())
    except Exception as exc:
        return _handle_error(exc)


async def maos_bus_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                _suite().bus_publish(
                    body.get("type") or "event",
                    sender=body.get("sender") or "agent_director",
                    recipient=body.get("recipient"),
                    payload=body.get("payload"),
                    priority=int(body.get("priority") or 5),
                    stream=bool(body.get("stream")),
                )
            )
        return json_response(_suite().bus())
    except Exception as exc:
        return _handle_error(exc)


async def maos_tasks_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
        return json_response(
            _suite().orchestrate(
                name=body.get("name") or "task",
                steps=body.get("steps"),
                mode=body.get("mode") or "sequential",
                timeout_ms=int(body.get("timeout_ms") or 5000),
                retry=int(body.get("retry") or 1),
                enable_rollback=bool(body.get("rollback")),
            )
        )
    except Exception as exc:
        return _handle_error(exc)


async def maos_memory_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                _suite().memory_write(
                    layer=body.get("layer") or "session",
                    content=body.get("content") or "",
                    meta=body.get("meta"),
                )
            )
        layer = request.rel_url.query.get("layer")
        return json_response(_suite().memory(layer))
    except Exception as exc:
        return _handle_error(exc)


async def maos_collaborate_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
        return json_response(
            _suite().collaborate(
                topic=body.get("topic") or "decision",
                action=body.get("action") or "discuss",
                proposals=body.get("proposals"),
            )
        )
    except Exception as exc:
        return _handle_error(exc)
