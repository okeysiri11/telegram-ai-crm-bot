"""API handlers — Platform Builder (Sprint 28.1)."""

from __future__ import annotations

from aiohttp import web

from applications.platform_builder import platform_builder
from applications.platform_builder.api.middleware import json_response
from applications.platform_builder.shared.exceptions import (
    ForbiddenError,
    NotFoundError,
    ValidationError,
)


def _handle_error(exc: Exception) -> web.Response:
    if isinstance(exc, ForbiddenError):
        return json_response({"error": str(exc)}, status=403)
    if isinstance(exc, NotFoundError):
        return json_response({"error": str(exc)}, status=404)
    if isinstance(exc, ValidationError):
        return json_response({"error": str(exc)}, status=400)
    return json_response({"error": str(exc)}, status=500)


def _role(request: web.Request) -> str | None:
    return request.get("platform_role")


async def health_handler(request: web.Request) -> web.Response:
    return json_response(platform_builder.health())


async def bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def inventory_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.inventory())
    except Exception as exc:
        return _handle_error(exc)


async def dashboard_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.dashboard())
    except Exception as exc:
        return _handle_error(exc)


async def builders_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.engine.list_builders())
    except Exception as exc:
        return _handle_error(exc)


async def builder_detail_handler(request: web.Request) -> web.Response:
    try:
        builder_id = request.match_info["builder_id"]
        return json_response(platform_builder.engine.describe(builder_id))
    except Exception as exc:
        return _handle_error(exc)


async def builder_preview_handler(request: web.Request) -> web.Response:
    try:
        builder_id = request.match_info["builder_id"]
        body = await request.json() if request.body_exists else {}
        return json_response(platform_builder.engine.preview(builder_id, body.get("payload") or body))
    except Exception as exc:
        return _handle_error(exc)


async def builder_create_handler(request: web.Request) -> web.Response:
    try:
        builder_id = request.match_info["builder_id"]
        body = await request.json() if request.body_exists else {}
        return json_response(
            platform_builder.engine.create(builder_id, body.get("payload") or body),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def academy_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            if "enabled" in body and body.get("builder_id"):
                return json_response(
                    platform_builder.academy.toggle_learning(
                        body["builder_id"], bool(body["enabled"])
                    )
                )
            mode = body.get("mode")
            if not mode:
                raise ValidationError("mode is required")
            return json_response(platform_builder.academy.set_mode(mode))
        return json_response(platform_builder.academy.status())
    except Exception as exc:
        return _handle_error(exc)


async def academy_guide_handler(request: web.Request) -> web.Response:
    try:
        builder_id = request.match_info["builder_id"]
        screen = request.rel_url.query.get("screen") or "Overview"
        return json_response(platform_builder.academy.screen_guide(builder_id, screen))
    except Exception as exc:
        return _handle_error(exc)


async def help_handler(request: web.Request) -> web.Response:
    try:
        builder_id = request.match_info["builder_id"]
        item = request.rel_url.query.get("item") or "Overview"
        return json_response(platform_builder.engine.help_for(builder_id, item))
    except Exception as exc:
        return _handle_error(exc)


async def menu_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.menu(_role(request)))
    except Exception as exc:
        return _handle_error(exc)


async def roles_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.roles())
    except Exception as exc:
        return _handle_error(exc)


async def god_mode_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.god_mode.status(_role(request)))
    except Exception as exc:
        return _handle_error(exc)


async def god_mode_action_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
        action = body.get("action")
        target = body.get("target")
        if not action or not target:
            raise ValidationError("action and target are required")
        return json_response(
            platform_builder.god_mode.action(
                _role(request),
                action=action,
                target=target,
                payload=body.get("payload"),
            )
        )
    except Exception as exc:
        return _handle_error(exc)
