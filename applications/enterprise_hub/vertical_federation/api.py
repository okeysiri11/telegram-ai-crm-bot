"""API handlers — Enterprise Vertical Federation (Sprint 27.3)."""

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
    return enterprise_hub.vertical_federation


async def vf_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "vertical_federation_ready": health.get("vertical_federation_ready"),
            "vertical_registry_ready": health.get("vertical_registry_ready"),
            "cross_vertical_communication_ready": health.get("cross_vertical_communication_ready"),
            "suite": _suite().status(),
        }
    )


async def vf_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def vf_inventory_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().inventory())
    except Exception as exc:
        return _handle_error(exc)


async def vf_dashboard_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().dashboard())
    except Exception as exc:
        return _handle_error(exc)


async def vf_registry_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            name = body.get("name")
            if not name:
                raise ValidationError("name is required")
            return json_response(
                _suite().register_custom(name=name, owner=body.get("owner")),
                status=201,
            )
        return json_response(_suite().registry())
    except Exception as exc:
        return _handle_error(exc)


async def vf_directors_handler(request: web.Request) -> web.Response:
    try:
        vertical = request.rel_url.query.get("vertical")
        return json_response(_suite().directors(vertical))
    except Exception as exc:
        return _handle_error(exc)


async def vf_director_act_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
        vertical = body.get("vertical")
        action = body.get("action")
        if not vertical or not action:
            raise ValidationError("vertical and action are required")
        return json_response(
            _suite().director_act(
                vertical=vertical,
                action=action,
                payload=body.get("payload"),
            )
        )
    except Exception as exc:
        return _handle_error(exc)


async def vf_links_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().links())
    except Exception as exc:
        return _handle_error(exc)


async def vf_communicate_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            source = body.get("source")
            target = body.get("target")
            message = body.get("message")
            if not source or not target or not message:
                raise ValidationError("source, target and message are required")
            return json_response(
                _suite().communicate(
                    source=source,
                    target=target,
                    message=message,
                    kind=body.get("kind") or "event",
                )
            )
        return json_response(_suite().messages())
    except Exception as exc:
        return _handle_error(exc)


async def vf_marketplace_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            vertical = body.get("vertical")
            asset_type = body.get("asset_type") or body.get("type")
            name = body.get("name")
            if not vertical or not asset_type or not name:
                raise ValidationError("vertical, asset_type and name are required")
            return json_response(
                _suite().marketplace_publish(
                    vertical=vertical,
                    asset_type=asset_type,
                    name=name,
                ),
                status=201,
            )
        vertical = request.rel_url.query.get("vertical")
        return json_response(_suite().marketplace(vertical))
    except Exception as exc:
        return _handle_error(exc)


async def vf_knowledge_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            content = body.get("content")
            if not content:
                raise ValidationError("content is required")
            return json_response(
                _suite().knowledge_write(
                    scope=body.get("scope") or "shared",
                    content=content,
                )
            )
        scope = request.rel_url.query.get("scope")
        return json_response(_suite().knowledge(scope))
    except Exception as exc:
        return _handle_error(exc)


async def vf_search_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json() if request.method == "POST" else {}
        query = body.get("query") or request.rel_url.query.get("q") or ""
        if not query:
            raise ValidationError("query is required")
        return json_response(_suite().semantic_search(query))
    except Exception as exc:
        return _handle_error(exc)
