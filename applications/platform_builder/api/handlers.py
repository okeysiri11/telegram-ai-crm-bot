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


async def ai_catalog_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.ai_builder.catalog())
    except Exception as exc:
        return _handle_error(exc)


async def ai_session_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.ai_builder.start_session(
                    agent_count=body.get("agent_count", 1),
                    custom_count=body.get("custom_count"),
                ),
                status=201,
            )
        session_id = request.match_info.get("session_id")
        if not session_id:
            raise ValidationError("session_id is required")
        if request.method == "PATCH":
            body = await request.json()
            return json_response(platform_builder.ai_builder.update_session(session_id, body))
        return json_response(platform_builder.ai_builder.get_session(session_id))
    except Exception as exc:
        return _handle_error(exc)


async def ai_names_handler(request: web.Request) -> web.Response:
    try:
        gender = request.rel_url.query.get("gender") or "neutral"
        return json_response(platform_builder.ai_builder.suggest_names(gender))
    except Exception as exc:
        return _handle_error(exc)


async def ai_specializations_handler(request: web.Request) -> web.Response:
    try:
        profession_id = request.match_info["profession_id"]
        return json_response(platform_builder.ai_builder.specializations(profession_id))
    except Exception as exc:
        return _handle_error(exc)


async def ai_personality_preview_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
        return json_response(
            platform_builder.ai_builder.personality_preview(
                body.get("personality") or {},
                name=body.get("name") or "Alex",
            )
        )
    except Exception as exc:
        return _handle_error(exc)


async def ai_summary_handler(request: web.Request) -> web.Response:
    try:
        session_id = request.match_info["session_id"]
        return json_response(platform_builder.ai_builder.summary(session_id))
    except Exception as exc:
        return _handle_error(exc)


async def ai_create_handler(request: web.Request) -> web.Response:
    try:
        session_id = request.match_info["session_id"]
        return json_response(platform_builder.ai_builder.create(session_id), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ai_registry_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.ai_builder.registry.list_agents())
    except Exception as exc:
        return _handle_error(exc)


async def ai_group_chat_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.ai_builder.registry.group_chat_foundation())
    except Exception as exc:
        return _handle_error(exc)


async def concierge_catalog_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.concierge.catalog())
    except Exception as exc:
        return _handle_error(exc)


async def concierge_session_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.concierge.start_session(
                    organization_id=body.get("organization_id") or "org_demo",
                ),
                status=201,
            )
        session_id = request.match_info.get("session_id")
        if not session_id:
            raise ValidationError("session_id is required")
        if request.method == "PATCH":
            body = await request.json()
            return json_response(platform_builder.concierge.update_session(session_id, body))
        return json_response(platform_builder.concierge.get_session(session_id))
    except Exception as exc:
        return _handle_error(exc)


async def concierge_preview_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
        return json_response(platform_builder.concierge.conversation_preview(body.get("draft") or body))
    except Exception as exc:
        return _handle_error(exc)


async def concierge_summary_handler(request: web.Request) -> web.Response:
    try:
        session_id = request.match_info["session_id"]
        return json_response(platform_builder.concierge.summary(session_id))
    except Exception as exc:
        return _handle_error(exc)


async def concierge_create_handler(request: web.Request) -> web.Response:
    try:
        session_id = request.match_info["session_id"]
        return json_response(platform_builder.concierge.create(session_id), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def concierge_registry_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.concierge.registry.list_all())
    except Exception as exc:
        return _handle_error(exc)


async def concierge_org_handler(request: web.Request) -> web.Response:
    try:
        organization_id = request.match_info["organization_id"]
        item = platform_builder.concierge.registry.get_for_organization(organization_id)
        if not item:
            return json_response({"organization_id": organization_id, "concierge": None})
        return json_response({"organization_id": organization_id, "concierge": item})
    except Exception as exc:
        return _handle_error(exc)


async def ai_team_dashboard_handler(request: web.Request) -> web.Response:
    try:
        organization_id = request.match_info.get("organization_id") or request.rel_url.query.get(
            "organization_id", "org_demo"
        )
        return json_response(platform_builder.ai_team.dashboard(organization_id))
    except Exception as exc:
        return _handle_error(exc)


async def ai_team_action_handler(request: web.Request) -> web.Response:
    try:
        organization_id = request.match_info["organization_id"]
        body = await request.json()
        agent_id = body.get("agent_id")
        action = body.get("action")
        if not agent_id or not action:
            raise ValidationError("agent_id and action are required")
        return json_response(
            platform_builder.ai_team.action(
                organization_id,
                agent_id,
                action,
                body.get("payload") or {},
            )
        )
    except Exception as exc:
        return _handle_error(exc)


async def ai_team_group_chat_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.ai_team.group_chat_foundation())
    except Exception as exc:
        return _handle_error(exc)


async def ai_team_status_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.ai_team.status())
    except Exception as exc:
        return _handle_error(exc)
