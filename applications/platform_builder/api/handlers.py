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


async def vertical_catalog_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.vertical.catalog())
    except Exception as exc:
        return _handle_error(exc)


async def vertical_session_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.vertical.start_session(
                    organization_id=body.get("organization_id") or "org_demo",
                ),
                status=201,
            )
        session_id = request.match_info.get("session_id")
        if not session_id:
            raise ValidationError("session_id is required")
        if request.method == "PATCH":
            body = await request.json()
            return json_response(platform_builder.vertical.update_session(session_id, body))
        return json_response(platform_builder.vertical.get_session(session_id))
    except Exception as exc:
        return _handle_error(exc)


async def vertical_preview_handler(request: web.Request) -> web.Response:
    try:
        session_id = request.match_info["session_id"]
        return json_response(platform_builder.vertical.organization_preview(session_id))
    except Exception as exc:
        return _handle_error(exc)


async def vertical_summary_handler(request: web.Request) -> web.Response:
    try:
        session_id = request.match_info["session_id"]
        return json_response(platform_builder.vertical.summary(session_id))
    except Exception as exc:
        return _handle_error(exc)


async def vertical_create_handler(request: web.Request) -> web.Response:
    try:
        session_id = request.match_info["session_id"]
        return json_response(platform_builder.vertical.create(session_id), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def vertical_registry_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.vertical.registry.list_all())
    except Exception as exc:
        return _handle_error(exc)


async def ubf_catalog_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.ubf.catalog())
    except Exception as exc:
        return _handle_error(exc)


async def ubf_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.ubf.bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ubf_session_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            return json_response(platform_builder.ubf.start_session(), status=201)
        session_id = request.match_info.get("session_id")
        if not session_id:
            raise ValidationError("session_id is required")
        if request.method == "PATCH":
            body = await request.json()
            return json_response(platform_builder.ubf.update_session(session_id, body))
        return json_response(platform_builder.ubf.get_session(session_id))
    except Exception as exc:
        return _handle_error(exc)


async def ubf_validate_handler(request: web.Request) -> web.Response:
    try:
        session_id = request.match_info["session_id"]
        return json_response(platform_builder.ubf.validate_session(session_id))
    except Exception as exc:
        return _handle_error(exc)


async def ubf_preview_handler(request: web.Request) -> web.Response:
    try:
        session_id = request.match_info["session_id"]
        return json_response(platform_builder.ubf.preview(session_id))
    except Exception as exc:
        return _handle_error(exc)


async def ubf_summary_handler(request: web.Request) -> web.Response:
    try:
        session_id = request.match_info["session_id"]
        return json_response(platform_builder.ubf.summary(session_id))
    except Exception as exc:
        return _handle_error(exc)


async def ubf_create_handler(request: web.Request) -> web.Response:
    try:
        session_id = request.match_info["session_id"]
        return json_response(platform_builder.ubf.create(session_id), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ubf_registry_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.ubf.registry.list_all())
    except Exception as exc:
        return _handle_error(exc)


async def ubf_templates_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(platform_builder.ubf.templates.save_template(body), status=201)
        return json_response(platform_builder.ubf.templates.list_all())
    except Exception as exc:
        return _handle_error(exc)


async def ubf_template_clone_handler(request: web.Request) -> web.Response:
    try:
        template_id = request.match_info["template_id"]
        body = await request.json() if request.body_exists else {}
        return json_response(
            platform_builder.ubf.templates.clone(template_id, new_name=body.get("name")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ubf_sdk_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.ubf.sdk.foundation())
    except Exception as exc:
        return _handle_error(exc)


async def ubf_sdk_define_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
        return json_response(platform_builder.ubf.sdk.define_builder(body), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def academy_v2_catalog_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.academy_v2.catalog())
    except Exception as exc:
        return _handle_error(exc)


async def academy_v2_session_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json() if request.body_exists else {}
            return json_response(
                platform_builder.academy_v2.start_session(user_id=body.get("user_id") or "owner"),
                status=201,
            )
        session_id = request.match_info.get("session_id")
        if not session_id:
            raise ValidationError("session_id is required")
        if request.method == "PATCH":
            body = await request.json()
            return json_response(platform_builder.academy_v2.update_session(session_id, body))
        return json_response(platform_builder.academy_v2.get_session(session_id))
    except Exception as exc:
        return _handle_error(exc)


async def academy_v2_summary_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.academy_v2.summary(request.match_info["session_id"]))
    except Exception as exc:
        return _handle_error(exc)


async def academy_v2_create_handler(request: web.Request) -> web.Response:
    try:
        return json_response(
            platform_builder.academy_v2.create(request.match_info["session_id"]),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def academy_v2_level_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.academy_v2.adapt_behavior(request.match_info["level"]))
    except Exception as exc:
        return _handle_error(exc)


async def academy_v2_help_handler(request: web.Request) -> web.Response:
    try:
        builder_id = request.rel_url.query.get("builder_id", "generic")
        return json_response(
            platform_builder.academy_v2.contextual_help(request.match_info["field"], builder_id)
        )
    except Exception as exc:
        return _handle_error(exc)


async def academy_v2_guide_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
        return json_response(
            platform_builder.academy_v2.guide.coach(
                builder_id=body.get("builder_id") or "generic",
                step=body.get("step") or "current",
                question=body.get("question"),
                draft=body.get("draft") or {},
                level=body.get("level") or "beginner",
            )
        )
    except Exception as exc:
        return _handle_error(exc)


async def academy_v2_guide_ask_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
        question = body.get("question")
        if not question:
            raise ValidationError("question is required")
        return json_response(
            platform_builder.academy_v2.guide.answer(
                question=question,
                builder_id=body.get("builder_id") or "generic",
                step=body.get("step") or "",
            )
        )
    except Exception as exc:
        return _handle_error(exc)


async def academy_v2_recs_handler(request: web.Request) -> web.Response:
    try:
        builder_id = request.rel_url.query.get("builder_id", "vertical")
        industry = request.rel_url.query.get("industry")
        return json_response(
            platform_builder.academy_v2.recommendations.recommend(
                builder_id=builder_id, industry=industry
            )
        )
    except Exception as exc:
        return _handle_error(exc)


async def academy_v2_analysis_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json() if request.body_exists else {}
        return json_response(
            platform_builder.academy_v2.live_analysis(
                body.get("draft") or {},
                builder_id=body.get("builder_id") or "generic",
            )
        )
    except Exception as exc:
        return _handle_error(exc)


async def academy_v2_impact_handler(request: web.Request) -> web.Response:
    try:
        option_id = request.match_info["option_id"]
        name = request.rel_url.query.get("name")
        return json_response(platform_builder.academy_v2.impact(option_id, name))
    except Exception as exc:
        return _handle_error(exc)


async def academy_v2_learning_handler(request: web.Request) -> web.Response:
    try:
        user_id = request.rel_url.query.get("user_id", "owner")
        return json_response(platform_builder.academy_v2.interactive_learning(user_id))
    except Exception as exc:
        return _handle_error(exc)


async def academy_v2_progress_handler(request: web.Request) -> web.Response:
    try:
        user_id = request.rel_url.query.get("user_id", "owner")
        return json_response(platform_builder.academy_v2.progress.snapshot(user_id))
    except Exception as exc:
        return _handle_error(exc)


# --- Sprint 28.7 — God Mode / Platform Control Center ---


async def control_catalog_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.control_center.catalog(_role(request)))
    except Exception as exc:
        return _handle_error(exc)


async def control_status_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.control_center.status(_role(request)))
    except Exception as exc:
        return _handle_error(exc)


async def control_overview_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.control_center.overview(_role(request)))
    except Exception as exc:
        return _handle_error(exc)


async def control_search_handler(request: web.Request) -> web.Response:
    try:
        q = request.rel_url.query.get("q") or request.rel_url.query.get("query") or ""
        scope = request.rel_url.query.get("scope")
        return json_response(platform_builder.control_center.search(_role(request), q, scope))
    except Exception as exc:
        return _handle_error(exc)


async def control_inspect_handler(request: web.Request) -> web.Response:
    try:
        return json_response(
            platform_builder.control_center.inspect(_role(request), request.match_info["object_id"])
        )
    except Exception as exc:
        return _handle_error(exc)


async def control_edit_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
        return json_response(
            platform_builder.control_center.edit(
                _role(request),
                request.match_info["object_id"],
                body.get("patch") or body,
            )
        )
    except Exception as exc:
        return _handle_error(exc)


async def control_registries_handler(request: web.Request) -> web.Response:
    try:
        action = request.rel_url.query.get("action")
        query = request.rel_url.query.get("q") or request.rel_url.query.get("query")
        if request.method == "POST":
            body = await request.json()
            action = body.get("action") or action
            query = body.get("query") or query
        return json_response(
            platform_builder.control_center.registries(
                _role(request), action=action, query=query
            )
        )
    except Exception as exc:
        return _handle_error(exc)


async def control_health_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.control_center.health(_role(request)))
    except Exception as exc:
        return _handle_error(exc)


async def control_diagnostics_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.control_center.diagnostics(_role(request)))
    except Exception as exc:
        return _handle_error(exc)


async def control_architecture_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.control_center.architecture(_role(request)))
    except Exception as exc:
        return _handle_error(exc)


async def control_audit_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.control_center.audit_center(_role(request)))
    except Exception as exc:
        return _handle_error(exc)


async def control_rollback_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
        version_id = body.get("version_id") or request.match_info.get("version_id") or "latest"
        return json_response(platform_builder.control_center.rollback(_role(request), version_id))
    except Exception as exc:
        return _handle_error(exc)


async def control_explain_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json() if request.method == "POST" else {}
        recommendation = (
            body.get("recommendation")
            or request.rel_url.query.get("recommendation")
            or "Synchronize registries"
        )
        return json_response(platform_builder.control_center.explain(_role(request), recommendation))
    except Exception as exc:
        return _handle_error(exc)


async def control_session_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            return json_response(
                platform_builder.control_center.start_session(_role(request)),
                status=201,
            )
        session_id = request.match_info.get("session_id")
        if not session_id:
            raise ValidationError("session_id is required")
        if request.method == "PATCH":
            body = await request.json()
            return json_response(
                platform_builder.control_center.update_session(_role(request), session_id, body)
            )
        return json_response(platform_builder.control_center.get_session(_role(request), session_id))
    except Exception as exc:
        return _handle_error(exc)


async def control_summary_handler(request: web.Request) -> web.Response:
    try:
        return json_response(
            platform_builder.control_center.summary(_role(request), request.match_info["session_id"])
        )
    except Exception as exc:
        return _handle_error(exc)


async def control_create_handler(request: web.Request) -> web.Response:
    try:
        return json_response(
            platform_builder.control_center.create(_role(request), request.match_info["session_id"]),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


# --- Sprint 28.8 — Collaborative AI / Collective Intelligence ---


async def collab_catalog_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.collaborative_ai.catalog())
    except Exception as exc:
        return _handle_error(exc)


async def collab_status_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.collaborative_ai.status())
    except Exception as exc:
        return _handle_error(exc)


async def collab_teams_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(platform_builder.collaborative_ai.create_team(body), status=201)
        return json_response(platform_builder.collaborative_ai.list_teams())
    except Exception as exc:
        return _handle_error(exc)


async def collab_team_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.collaborative_ai.get_team(request.match_info["team_id"]))
    except Exception as exc:
        return _handle_error(exc)


async def collab_roles_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json() if request.can_read_body else {}
        assignments = body.get("assignments") if isinstance(body, dict) else None
        return json_response(
            platform_builder.collaborative_ai.assign_roles(
                request.match_info["team_id"], assignments
            )
        )
    except Exception as exc:
        return _handle_error(exc)


async def collab_team_session_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json() if request.can_read_body else {}
        topic = body.get("topic") if isinstance(body, dict) else None
        return json_response(
            platform_builder.collaborative_ai.start_collab_session(
                request.match_info["team_id"], topic=topic
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def collab_workspace_handler(request: web.Request) -> web.Response:
    try:
        return json_response(
            platform_builder.collaborative_ai.session_workspace(request.match_info["session_id"])
        )
    except Exception as exc:
        return _handle_error(exc)


async def collab_tasks_handler(request: web.Request) -> web.Response:
    try:
        return json_response(
            platform_builder.collaborative_ai.distribute_tasks(request.match_info["session_id"])
        )
    except Exception as exc:
        return _handle_error(exc)


async def collab_knowledge_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json() if request.can_read_body else {}
        entries = body.get("entries") if isinstance(body, dict) else None
        return json_response(
            platform_builder.collaborative_ai.share_knowledge(
                request.match_info["session_id"], entries
            )
        )
    except Exception as exc:
        return _handle_error(exc)


async def collab_decide_handler(request: web.Request) -> web.Response:
    try:
        return json_response(
            platform_builder.collaborative_ai.decide(request.match_info["session_id"])
        )
    except Exception as exc:
        return _handle_error(exc)


async def collab_report_handler(request: web.Request) -> web.Response:
    try:
        return json_response(
            platform_builder.collaborative_ai.executive_summary(request.match_info["session_id"])
        )
    except Exception as exc:
        return _handle_error(exc)


async def collab_performance_handler(request: web.Request) -> web.Response:
    try:
        return json_response(
            platform_builder.collaborative_ai.performance(request.match_info["session_id"])
        )
    except Exception as exc:
        return _handle_error(exc)


async def collab_explain_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json() if request.method == "POST" and request.can_read_body else {}
        recommendation = body.get("recommendation") if isinstance(body, dict) else None
        if not recommendation:
            recommendation = request.rel_url.query.get("recommendation")
        return json_response(
            platform_builder.collaborative_ai.explain_decision(
                request.match_info["session_id"], recommendation
            )
        )
    except Exception as exc:
        return _handle_error(exc)


async def collab_ops_handler(request: web.Request) -> web.Response:
    try:
        team_id = request.rel_url.query.get("team_id")
        session_id = request.rel_url.query.get("session_id")
        return json_response(
            platform_builder.collaborative_ai.ops_foundation(team_id=team_id, session_id=session_id)
        )
    except Exception as exc:
        return _handle_error(exc)


async def collab_wizard_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.collaborative_ai.start_wizard(owner_id=body.get("owner_id")),
                status=201,
            )
        session_id = request.match_info.get("session_id")
        if not session_id:
            raise ValidationError("session_id is required")
        if request.method == "PATCH":
            body = await request.json()
            return json_response(
                platform_builder.collaborative_ai.update_wizard(session_id, body)
            )
        return json_response(platform_builder.collaborative_ai.get_wizard(session_id))
    except Exception as exc:
        return _handle_error(exc)


async def collab_wizard_summary_handler(request: web.Request) -> web.Response:
    try:
        return json_response(
            platform_builder.collaborative_ai.summary(request.match_info["session_id"])
        )
    except Exception as exc:
        return _handle_error(exc)


async def collab_wizard_create_handler(request: web.Request) -> web.Response:
    try:
        return json_response(
            platform_builder.collaborative_ai.create(request.match_info["session_id"]),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


# --- Sprint 29.1 — Enterprise AI Operations Center ---


async def ops_catalog_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.operations_center.catalog())
    except Exception as exc:
        return _handle_error(exc)


async def ops_status_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.operations_center.status())
    except Exception as exc:
        return _handle_error(exc)


async def ops_dashboard_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.operations_center.dashboard())
    except Exception as exc:
        return _handle_error(exc)


async def ops_live_status_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.operations_center.live_status())
    except Exception as exc:
        return _handle_error(exc)


async def ops_activity_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.operations_center.realtime_activity())
    except Exception as exc:
        return _handle_error(exc)


async def ops_visual_ids_handler(request: web.Request) -> web.Response:
    try:
        object_id = request.rel_url.query.get("object_id") or request.match_info.get("object_id")
        return json_response(platform_builder.operations_center.visual_ids(object_id))
    except Exception as exc:
        return _handle_error(exc)


async def ops_wait_handler(request: web.Request) -> web.Response:
    try:
        process_id = request.rel_url.query.get("process_id")
        return json_response(platform_builder.operations_center.wait_experience(process_id))
    except Exception as exc:
        return _handle_error(exc)


async def ops_teams_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.operations_center.team_overview())
    except Exception as exc:
        return _handle_error(exc)


async def ops_health_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.operations_center.system_health())
    except Exception as exc:
        return _handle_error(exc)


async def ops_city_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.operations_center.ai_city_foundation())
    except Exception as exc:
        return _handle_error(exc)


async def ops_summary_view_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.operations_center.ops_summary())
    except Exception as exc:
        return _handle_error(exc)


async def ops_visual_layer_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.operations_center.visual.catalog())
    except Exception as exc:
        return _handle_error(exc)


async def ops_session_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            return json_response(platform_builder.operations_center.start_session(), status=201)
        session_id = request.match_info.get("session_id")
        if not session_id:
            raise ValidationError("session_id is required")
        if request.method == "PATCH":
            body = await request.json()
            return json_response(platform_builder.operations_center.update_session(session_id, body))
        return json_response(platform_builder.operations_center.get_session(session_id))
    except Exception as exc:
        return _handle_error(exc)


async def ops_session_summary_handler(request: web.Request) -> web.Response:
    try:
        return json_response(
            platform_builder.operations_center.summary(request.match_info["session_id"])
        )
    except Exception as exc:
        return _handle_error(exc)


async def ops_create_handler(request: web.Request) -> web.Response:
    try:
        return json_response(
            platform_builder.operations_center.create(request.match_info["session_id"]),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


# --- Sprint 29.2 — AI Team Map / Live Organization ---


async def team_map_catalog_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.team_map.catalog())
    except Exception as exc:
        return _handle_error(exc)


async def team_map_status_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.team_map.status())
    except Exception as exc:
        return _handle_error(exc)


async def team_map_view_handler(request: web.Request) -> web.Response:
    try:
        return json_response(
            platform_builder.team_map.map_view(
                department=request.rel_url.query.get("department"),
                search=request.rel_url.query.get("search") or request.rel_url.query.get("q"),
                status=request.rel_url.query.get("status"),
            )
        )
    except Exception as exc:
        return _handle_error(exc)


async def team_map_cards_handler(request: web.Request) -> web.Response:
    try:
        return json_response(
            platform_builder.team_map.ai_cards(request.rel_url.query.get("department"))
        )
    except Exception as exc:
        return _handle_error(exc)


async def team_map_live_status_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.team_map.live_status())
    except Exception as exc:
        return _handle_error(exc)


async def team_map_workload_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.team_map.workload_overview())
    except Exception as exc:
        return _handle_error(exc)


async def team_map_relationships_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.team_map.relationship_map())
    except Exception as exc:
        return _handle_error(exc)


async def team_map_activity_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.team_map.live_activity())
    except Exception as exc:
        return _handle_error(exc)


async def team_map_bus_subscribe_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json() if request.can_read_body else {}
        channels = body.get("channels") if isinstance(body, dict) else None
        return json_response(platform_builder.team_map.bus_subscribe(channels), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def team_map_bus_poll_handler(request: web.Request) -> web.Response:
    try:
        return json_response(
            platform_builder.team_map.bus_poll(request.rel_url.query.get("since"))
        )
    except Exception as exc:
        return _handle_error(exc)


async def team_map_visual_objects_handler(request: web.Request) -> web.Response:
    try:
        object_id = request.match_info.get("object_id") or request.rel_url.query.get("object_id")
        return json_response(platform_builder.team_map.visual_objects(object_id))
    except Exception as exc:
        return _handle_error(exc)


async def team_map_city_apis_handler(request: web.Request) -> web.Response:
    try:
        return json_response(
            platform_builder.team_map.ai_city_apis(request.rel_url.query.get("logical_id"))
        )
    except Exception as exc:
        return _handle_error(exc)


async def team_map_session_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            return json_response(platform_builder.team_map.start_session(), status=201)
        session_id = request.match_info.get("session_id")
        if not session_id:
            raise ValidationError("session_id is required")
        if request.method == "PATCH":
            body = await request.json()
            return json_response(platform_builder.team_map.update_session(session_id, body))
        return json_response(platform_builder.team_map.get_session(session_id))
    except Exception as exc:
        return _handle_error(exc)


async def team_map_session_summary_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.team_map.summary(request.match_info["session_id"]))
    except Exception as exc:
        return _handle_error(exc)


async def team_map_create_handler(request: web.Request) -> web.Response:
    try:
        return json_response(
            platform_builder.team_map.create(request.match_info["session_id"]),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


# --- Sprint 29.3 — Visual Behavior Engine / Animation Framework ---


async def vb_catalog_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.visual_behavior.catalog())
    except Exception as exc:
        return _handle_error(exc)


async def vb_status_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.visual_behavior.status())
    except Exception as exc:
        return _handle_error(exc)


async def vb_overview_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.visual_behavior.engine_overview())
    except Exception as exc:
        return _handle_error(exc)


async def vb_behaviors_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.visual_behavior.list_behaviors())
    except Exception as exc:
        return _handle_error(exc)


async def vb_transitions_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.visual_behavior.transition_catalog())
    except Exception as exc:
        return _handle_error(exc)


async def vb_transition_run_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
        logical_id = body.get("logical_id") or request.match_info.get("logical_id")
        to_behavior = body.get("to") or body.get("to_behavior")
        if not logical_id or not to_behavior:
            raise ValidationError("logical_id and to_behavior are required")
        return json_response(platform_builder.visual_behavior.run_transition(logical_id, to_behavior))
    except Exception as exc:
        return _handle_error(exc)


async def vb_animations_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.visual_behavior.animation_framework())
    except Exception as exc:
        return _handle_error(exc)


async def vb_play_animation_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
        animation = body.get("animation")
        if not animation:
            raise ValidationError("animation is required")
        return json_response(
            platform_builder.visual_behavior.play_animation(
                animation, target_id=body.get("target_id")
            )
        )
    except Exception as exc:
        return _handle_error(exc)


async def vb_object_types_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.visual_behavior.object_types())
    except Exception as exc:
        return _handle_error(exc)


async def vb_objects_handler(request: web.Request) -> web.Response:
    try:
        object_id = request.match_info.get("logical_id")
        if object_id:
            return json_response(platform_builder.visual_behavior.get_object(object_id))
        return json_response(platform_builder.visual_behavior.list_objects())
    except Exception as exc:
        return _handle_error(exc)


async def vb_subscribe_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json() if request.can_read_body else {}
        channels = body.get("channels") if isinstance(body, dict) else None
        return json_response(platform_builder.visual_behavior.subscribe_events(channels), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def vb_poll_handler(request: web.Request) -> web.Response:
    try:
        return json_response(
            platform_builder.visual_behavior.poll_events(request.rel_url.query.get("since"))
        )
    except Exception as exc:
        return _handle_error(exc)


async def vb_wait_handler(request: web.Request) -> web.Response:
    try:
        return json_response(
            platform_builder.visual_behavior.wait_experience(
                request.rel_url.query.get("process_id")
            )
        )
    except Exception as exc:
        return _handle_error(exc)


async def vb_performance_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.visual_behavior.performance())
    except Exception as exc:
        return _handle_error(exc)


async def vb_city_apis_handler(request: web.Request) -> web.Response:
    try:
        return json_response(
            platform_builder.visual_behavior.ai_city_apis(request.rel_url.query.get("logical_id"))
        )
    except Exception as exc:
        return _handle_error(exc)


async def vb_session_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            return json_response(platform_builder.visual_behavior.start_session(), status=201)
        session_id = request.match_info.get("session_id")
        if not session_id:
            raise ValidationError("session_id is required")
        if request.method == "PATCH":
            body = await request.json()
            return json_response(platform_builder.visual_behavior.update_session(session_id, body))
        return json_response(platform_builder.visual_behavior.get_session(session_id))
    except Exception as exc:
        return _handle_error(exc)


async def vb_session_summary_handler(request: web.Request) -> web.Response:
    try:
        return json_response(
            platform_builder.visual_behavior.summary(request.match_info["session_id"])
        )
    except Exception as exc:
        return _handle_error(exc)


async def vb_create_handler(request: web.Request) -> web.Response:
    try:
        return json_response(
            platform_builder.visual_behavior.create(request.match_info["session_id"]),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


# --- Sprint 29.4 — Visual Rendering Engine / LOD / Viewport ---


async def render_catalog_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.rendering.catalog())
    except Exception as exc:
        return _handle_error(exc)


async def render_status_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.rendering.status())
    except Exception as exc:
        return _handle_error(exc)


async def render_renderer_handler(request: web.Request) -> web.Response:
    try:
        zoom = float(request.rel_url.query.get("zoom") or 1.0)
        return json_response(platform_builder.rendering.renderer(zoom=zoom))
    except Exception as exc:
        return _handle_error(exc)


async def render_lod_handler(request: web.Request) -> web.Response:
    try:
        zoom = float(request.rel_url.query.get("zoom") or 1.0)
        return json_response(platform_builder.rendering.lod_view(zoom))
    except Exception as exc:
        return _handle_error(exc)


async def render_viewport_handler(request: web.Request) -> web.Response:
    try:
        q = request.rel_url.query
        return json_response(
            platform_builder.rendering.viewport_view(
                x=float(q.get("x") or 0),
                y=float(q.get("y") or 0),
                width=float(q.get("width") or 800),
                height=float(q.get("height") or 600),
                zoom=float(q.get("zoom") or 1.0),
            )
        )
    except Exception as exc:
        return _handle_error(exc)


async def render_layers_handler(request: web.Request) -> web.Response:
    try:
        zoom = float(request.rel_url.query.get("zoom") or 1.0)
        return json_response(platform_builder.rendering.layer_system(zoom))
    except Exception as exc:
        return _handle_error(exc)


async def render_priorities_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.rendering.priorities())
    except Exception as exc:
        return _handle_error(exc)


async def render_anim_opt_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.rendering.animation_optimization())
    except Exception as exc:
        return _handle_error(exc)


async def render_live_org_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.rendering.live_organization_support())
    except Exception as exc:
        return _handle_error(exc)


async def render_city_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.rendering.ai_city_foundation())
    except Exception as exc:
        return _handle_error(exc)


async def render_perf_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.rendering.performance())
    except Exception as exc:
        return _handle_error(exc)


async def render_sync_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.rendering.sync_from_sources())
    except Exception as exc:
        return _handle_error(exc)


async def render_session_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            return json_response(platform_builder.rendering.start_session(), status=201)
        session_id = request.match_info.get("session_id")
        if not session_id:
            raise ValidationError("session_id is required")
        if request.method == "PATCH":
            body = await request.json()
            return json_response(platform_builder.rendering.update_session(session_id, body))
        return json_response(platform_builder.rendering.get_session(session_id))
    except Exception as exc:
        return _handle_error(exc)


async def render_session_summary_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.rendering.summary(request.match_info["session_id"]))
    except Exception as exc:
        return _handle_error(exc)


async def render_create_handler(request: web.Request) -> web.Response:
    try:
        return json_response(
            platform_builder.rendering.create(request.match_info["session_id"]),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


# --- Sprint 29.5 — Visual Theme Engine / Branding ---


async def theme_catalog_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.themes.catalog())
    except Exception as exc:
        return _handle_error(exc)


async def theme_status_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.themes.status())
    except Exception as exc:
        return _handle_error(exc)


async def theme_engine_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.themes.theme_engine_overview())
    except Exception as exc:
        return _handle_error(exc)


async def theme_colors_handler(request: web.Request) -> web.Response:
    try:
        mode = request.rel_url.query.get("mode") or "dark"
        return json_response(platform_builder.themes.color_system(mode))
    except Exception as exc:
        return _handle_error(exc)


async def theme_branding_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(platform_builder.themes.upsert_brand_profile(body), status=201)
        org = request.rel_url.query.get("organization_id")
        return json_response(platform_builder.themes.branding(org))
    except Exception as exc:
        return _handle_error(exc)


async def theme_components_handler(request: web.Request) -> web.Response:
    try:
        theme_id = request.rel_url.query.get("theme_id")
        return json_response(platform_builder.themes.component_theming(theme_id))
    except Exception as exc:
        return _handle_error(exc)


async def theme_ai_style_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.themes.ai_visual_style())
    except Exception as exc:
        return _handle_error(exc)


async def theme_animation_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.themes.animation_themes())
    except Exception as exc:
        return _handle_error(exc)


async def theme_a11y_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.themes.accessibility())
    except Exception as exc:
        return _handle_error(exc)


async def theme_active_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.themes.active_theme())
    except Exception as exc:
        return _handle_error(exc)


async def theme_switch_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
        theme_id = body.get("theme_id")
        if not theme_id:
            raise ValidationError("theme_id is required")
        return json_response(platform_builder.themes.live_switch(theme_id))
    except Exception as exc:
        return _handle_error(exc)


async def theme_registry_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.themes.registry.list_themes())
    except Exception as exc:
        return _handle_error(exc)


async def theme_city_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.themes.ai_city_foundation())
    except Exception as exc:
        return _handle_error(exc)


async def theme_session_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            return json_response(platform_builder.themes.start_session(), status=201)
        session_id = request.match_info.get("session_id")
        if not session_id:
            raise ValidationError("session_id is required")
        if request.method == "PATCH":
            body = await request.json()
            return json_response(platform_builder.themes.update_session(session_id, body))
        return json_response(platform_builder.themes.get_session(session_id))
    except Exception as exc:
        return _handle_error(exc)


async def theme_session_summary_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.themes.summary(request.match_info["session_id"]))
    except Exception as exc:
        return _handle_error(exc)


async def theme_create_handler(request: web.Request) -> web.Response:
    try:
        return json_response(
            platform_builder.themes.create(request.match_info["session_id"]),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


# --- Sprint 29.6 — Visual Asset Registry / Resource Management ---


async def asset_catalog_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.assets.catalog())
    except Exception as exc:
        return _handle_error(exc)


async def asset_status_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.assets.status())
    except Exception as exc:
        return _handle_error(exc)


async def asset_registry_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.assets.registry_overview())
    except Exception as exc:
        return _handle_error(exc)


async def asset_categories_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.assets.categories())
    except Exception as exc:
        return _handle_error(exc)


async def asset_versions_handler(request: web.Request) -> web.Response:
    try:
        asset_id = request.rel_url.query.get("asset_id")
        return json_response(platform_builder.assets.version_management(asset_id))
    except Exception as exc:
        return _handle_error(exc)


async def asset_replace_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
        asset_id = body.get("asset_id") or request.match_info.get("asset_id")
        if not asset_id:
            raise ValidationError("asset_id is required")
        return json_response(platform_builder.assets.replace_asset(asset_id, body))
    except Exception as exc:
        return _handle_error(exc)


async def asset_rollback_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
        asset_id = body.get("asset_id")
        if not asset_id:
            raise ValidationError("asset_id is required")
        revision = body.get("revision")
        return json_response(
            platform_builder.assets.rollback_asset(
                asset_id, int(revision) if revision is not None else None
            )
        )
    except Exception as exc:
        return _handle_error(exc)


async def asset_optimization_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.assets.resource_optimization())
    except Exception as exc:
        return _handle_error(exc)


async def asset_avatars_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.assets.avatar_library())
    except Exception as exc:
        return _handle_error(exc)


async def asset_branding_handler(request: web.Request) -> web.Response:
    try:
        org = request.rel_url.query.get("organization_id")
        return json_response(platform_builder.assets.organization_branding(org))
    except Exception as exc:
        return _handle_error(exc)


async def asset_city_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.assets.ai_city_foundation())
    except Exception as exc:
        return _handle_error(exc)


async def asset_search_handler(request: web.Request) -> web.Response:
    try:
        q = request.rel_url.query
        filters = {
            k: q.get(k)
            for k in (
                "category",
                "organization_id",
                "department_id",
                "asset_type",
                "type",
                "theme_id",
                "theme",
                "tags",
                "q",
            )
            if q.get(k)
        }
        return json_response(platform_builder.assets.search(filters))
    except Exception as exc:
        return _handle_error(exc)


async def asset_performance_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.assets.performance())
    except Exception as exc:
        return _handle_error(exc)


async def asset_browser_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.assets.browser())
    except Exception as exc:
        return _handle_error(exc)


async def asset_preview_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.assets.preview(request.match_info["asset_id"]))
    except Exception as exc:
        return _handle_error(exc)


async def asset_session_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            return json_response(platform_builder.assets.start_session(), status=201)
        session_id = request.match_info.get("session_id")
        if not session_id:
            raise ValidationError("session_id is required")
        if request.method == "PATCH":
            body = await request.json()
            return json_response(platform_builder.assets.update_session(session_id, body))
        return json_response(platform_builder.assets.get_session(session_id))
    except Exception as exc:
        return _handle_error(exc)


async def asset_session_summary_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.assets.summary(request.match_info["session_id"]))
    except Exception as exc:
        return _handle_error(exc)


async def asset_create_handler(request: web.Request) -> web.Response:
    try:
        return json_response(
            platform_builder.assets.create(request.match_info["session_id"]),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


# --- Sprint 29.7 — Visual Simulation Engine / Live Enterprise Simulation ---


async def sim_catalog_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.simulation.catalog())
    except Exception as exc:
        return _handle_error(exc)


async def sim_status_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.simulation.status())
    except Exception as exc:
        return _handle_error(exc)


async def sim_engine_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.simulation.engine_overview())
    except Exception as exc:
        return _handle_error(exc)


async def sim_supported_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.simulation.supported_simulations())
    except Exception as exc:
        return _handle_error(exc)


async def sim_live_org_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.simulation.live_organization_simulation())
    except Exception as exc:
        return _handle_error(exc)


async def sim_collab_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.simulation.ai_collaboration())
    except Exception as exc:
        return _handle_error(exc)


async def sim_workflow_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.simulation.workflow_simulation())
    except Exception as exc:
        return _handle_error(exc)


async def sim_knowledge_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.simulation.knowledge_flow())
    except Exception as exc:
        return _handle_error(exc)


async def sim_document_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.simulation.document_flow())
    except Exception as exc:
        return _handle_error(exc)


async def sim_timeline_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            return json_response(platform_builder.simulation.timeline.status())
        body = await request.json()
        action = body.get("action") or "pause"
        speed = body.get("speed")
        return json_response(
            platform_builder.simulation.timeline_control(
                action, speed=float(speed) if speed is not None else None
            )
        )
    except Exception as exc:
        return _handle_error(exc)


async def sim_performance_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.simulation.performance())
    except Exception as exc:
        return _handle_error(exc)


async def sim_ui_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.simulation.ui_dashboard())
    except Exception as exc:
        return _handle_error(exc)


async def sim_ingest_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.simulation.ingest_from_bus())
    except Exception as exc:
        return _handle_error(exc)


async def sim_emit_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
        name = body.get("simulation") or body.get("name")
        if not name:
            raise ValidationError("simulation is required")
        return json_response(
            platform_builder.simulation.emit_and_simulate(name, body.get("payload")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def sim_session_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            return json_response(platform_builder.simulation.start_session(), status=201)
        session_id = request.match_info.get("session_id")
        if not session_id:
            raise ValidationError("session_id is required")
        if request.method == "PATCH":
            body = await request.json()
            return json_response(platform_builder.simulation.update_session(session_id, body))
        return json_response(platform_builder.simulation.get_session(session_id))
    except Exception as exc:
        return _handle_error(exc)


async def sim_session_summary_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.simulation.summary(request.match_info["session_id"]))
    except Exception as exc:
        return _handle_error(exc)


async def sim_create_handler(request: web.Request) -> web.Response:
    try:
        return json_response(
            platform_builder.simulation.create(request.match_info["session_id"]),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


# --- Sprint 29.8 — Visual Director Engine / Scene Orchestration ---


async def dir_catalog_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.director.catalog())
    except Exception as exc:
        return _handle_error(exc)


async def dir_status_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.director.status())
    except Exception as exc:
        return _handle_error(exc)


async def dir_engine_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.director.director_overview())
    except Exception as exc:
        return _handle_error(exc)


async def dir_scenes_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            name = body.get("name") or "Untitled Scene"
            kind = body.get("kind") or "live_organization"
            scene = platform_builder.director.scenes.create_scene(name, kind=kind)
            return json_response(scene, status=201)
        return json_response(platform_builder.director.scene_management())
    except Exception as exc:
        return _handle_error(exc)


async def dir_scene_switch_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
        scene_id = body.get("scene_id")
        if not scene_id:
            raise ValidationError("scene_id is required")
        return json_response(platform_builder.director.scenes.switch_scene(scene_id))
    except Exception as exc:
        return _handle_error(exc)


async def dir_scene_sync_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
        scene_id = body.get("scene_id")
        if not scene_id:
            raise ValidationError("scene_id is required")
        return json_response(
            platform_builder.director.scenes.synchronize(scene_id, body.get("engines"))
        )
    except Exception as exc:
        return _handle_error(exc)


async def dir_focus_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.director.focus_engine())
    except Exception as exc:
        return _handle_error(exc)


async def dir_attention_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.director.attention_management())
    except Exception as exc:
        return _handle_error(exc)


async def dir_coordination_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.director.simulation_coordination())
    except Exception as exc:
        return _handle_error(exc)


async def dir_live_org_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.director.live_organization())
    except Exception as exc:
        return _handle_error(exc)


async def dir_camera_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.director.camera_api(
                    position=body.get("position"),
                    tracking=body.get("tracking"),
                    zoom=body.get("zoom"),
                    focus_target=body.get("focus_target"),
                )
            )
        return json_response(platform_builder.director.camera_api())
    except Exception as exc:
        return _handle_error(exc)


async def dir_conflicts_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.director.conflict_resolution())
    except Exception as exc:
        return _handle_error(exc)


async def dir_performance_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.director.performance())
    except Exception as exc:
        return _handle_error(exc)


async def dir_ui_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.director.ui_dashboard())
    except Exception as exc:
        return _handle_error(exc)


async def dir_session_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            return json_response(platform_builder.director.start_session(), status=201)
        session_id = request.match_info.get("session_id")
        if not session_id:
            raise ValidationError("session_id is required")
        if request.method == "PATCH":
            body = await request.json()
            return json_response(platform_builder.director.update_session(session_id, body))
        return json_response(platform_builder.director.get_session(session_id))
    except Exception as exc:
        return _handle_error(exc)


async def dir_session_summary_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.director.summary(request.match_info["session_id"]))
    except Exception as exc:
        return _handle_error(exc)


async def dir_create_handler(request: web.Request) -> web.Response:
    try:
        return json_response(
            platform_builder.director.create(request.match_info["session_id"]),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


# --- Sprint 29.9 — Visual Story Engine / Enterprise Storytelling ---


async def story_catalog_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.story.catalog())
    except Exception as exc:
        return _handle_error(exc)


async def story_status_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.story.status())
    except Exception as exc:
        return _handle_error(exc)


async def story_engine_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.story.engine_overview())
    except Exception as exc:
        return _handle_error(exc)


async def story_types_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.story.story_types())
    except Exception as exc:
        return _handle_error(exc)


async def story_segments_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.story.story_segments())
    except Exception as exc:
        return _handle_error(exc)


async def story_build_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
        story_type = body.get("story_type") or body.get("type")
        if not story_type:
            raise ValidationError("story_type is required")
        return json_response(
            platform_builder.story.build_story(
                story_type, title=body.get("title"), persist=body.get("persist", True)
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def story_org_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.story.organization_evolution())
    except Exception as exc:
        return _handle_error(exc)


async def story_ai_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.story.ai_stories())
    except Exception as exc:
        return _handle_error(exc)


async def story_workflow_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.story.workflow_stories())
    except Exception as exc:
        return _handle_error(exc)


async def story_knowledge_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.story.knowledge_stories())
    except Exception as exc:
        return _handle_error(exc)


async def story_executive_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.story.executive_mode())
    except Exception as exc:
        return _handle_error(exc)


async def story_navigate_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
        action = body.get("action")
        if not action:
            raise ValidationError("action is required")
        return json_response(
            platform_builder.story.navigate(
                action, index=body.get("index"), label=body.get("label")
            )
        )
    except Exception as exc:
        return _handle_error(exc)


async def story_timeline_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.story.timeline.status())
    except Exception as exc:
        return _handle_error(exc)


async def story_milestones_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.story.milestone_viewer())
    except Exception as exc:
        return _handle_error(exc)


async def story_history_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.story.story_history())
    except Exception as exc:
        return _handle_error(exc)


async def story_ui_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.story.ui_dashboard())
    except Exception as exc:
        return _handle_error(exc)


async def story_session_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            return json_response(platform_builder.story.start_session(), status=201)
        session_id = request.match_info.get("session_id")
        if not session_id:
            raise ValidationError("session_id is required")
        if request.method == "PATCH":
            body = await request.json()
            return json_response(platform_builder.story.update_session(session_id, body))
        return json_response(platform_builder.story.get_session(session_id))
    except Exception as exc:
        return _handle_error(exc)


async def story_session_summary_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.story.summary(request.match_info["session_id"]))
    except Exception as exc:
        return _handle_error(exc)


async def story_create_handler(request: web.Request) -> web.Response:
    try:
        return json_response(
            platform_builder.story.create(request.match_info["session_id"]),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


# --- Sprint 29.10 — Visual Intelligence Engine / Enterprise Visual Analytics ---


async def intel_catalog_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.intelligence.catalog())
    except Exception as exc:
        return _handle_error(exc)


async def intel_status_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.intelligence.status())
    except Exception as exc:
        return _handle_error(exc)


async def intel_engine_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.intelligence.engine_overview())
    except Exception as exc:
        return _handle_error(exc)


async def intel_patterns_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.intelligence.pattern_detection())
    except Exception as exc:
        return _handle_error(exc)


async def intel_anomalies_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.intelligence.anomaly_detection())
    except Exception as exc:
        return _handle_error(exc)


async def intel_recommendations_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.intelligence.attention_recommendations())
    except Exception as exc:
        return _handle_error(exc)


async def intel_executive_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.intelligence.executive_insights())
    except Exception as exc:
        return _handle_error(exc)


async def intel_heatmaps_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.intelligence.visual_heatmaps())
    except Exception as exc:
        return _handle_error(exc)


async def intel_trends_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.intelligence.trend_engine())
    except Exception as exc:
        return _handle_error(exc)


async def intel_health_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.intelligence.visual_health_index())
    except Exception as exc:
        return _handle_error(exc)


async def intel_predictive_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.intelligence.predictive_foundation())
    except Exception as exc:
        return _handle_error(exc)


async def intel_analyze_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.intelligence.analyze_snapshot(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def intel_ui_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.intelligence.ui_dashboard())
    except Exception as exc:
        return _handle_error(exc)


async def intel_session_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            return json_response(platform_builder.intelligence.start_session(), status=201)
        session_id = request.match_info.get("session_id")
        if not session_id:
            raise ValidationError("session_id is required")
        if request.method == "PATCH":
            body = await request.json()
            return json_response(platform_builder.intelligence.update_session(session_id, body))
        return json_response(platform_builder.intelligence.get_session(session_id))
    except Exception as exc:
        return _handle_error(exc)


async def intel_session_summary_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.intelligence.summary(request.match_info["session_id"]))
    except Exception as exc:
        return _handle_error(exc)


async def intel_create_handler(request: web.Request) -> web.Response:
    try:
        return json_response(
            platform_builder.intelligence.create(request.match_info["session_id"]),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


# --- Sprint 29.11 — Visual Experience Engine / Unified Enterprise UX ---


async def experience_catalog_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.experience.catalog())
    except Exception as exc:
        return _handle_error(exc)


async def experience_status_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.experience.status())
    except Exception as exc:
        return _handle_error(exc)


async def experience_engine_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.experience.engine_overview())
    except Exception as exc:
        return _handle_error(exc)


async def experience_unified_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.experience.unified_experience())
    except Exception as exc:
        return _handle_error(exc)


async def experience_context_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.experience.user_context(body.get("context")),
                status=201,
            )
        context = request.rel_url.query.get("context")
        return json_response(platform_builder.experience.user_context(context))
    except Exception as exc:
        return _handle_error(exc)


async def experience_adaptive_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "PATCH":
            body = await request.json()
            return json_response(platform_builder.experience.adaptive_interface(body))
        return json_response(platform_builder.experience.adaptive_interface())
    except Exception as exc:
        return _handle_error(exc)


async def experience_transitions_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.experience.transitions(
                    body.get("type"),
                    body.get("target"),
                ),
                status=201,
            )
        return json_response(platform_builder.experience.transitions())
    except Exception as exc:
        return _handle_error(exc)


async def experience_rules_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.experience.global_rules())
    except Exception as exc:
        return _handle_error(exc)


async def experience_cognitive_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.experience.cognitive_load_control())
    except Exception as exc:
        return _handle_error(exc)


async def experience_workspaces_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.experience.multi_workspace(
                    action=body.get("action"),
                    workspace_id=body.get("workspace_id"),
                    name=body.get("name"),
                    memory=body.get("memory"),
                ),
                status=201,
            )
        return json_response(platform_builder.experience.multi_workspace())
    except Exception as exc:
        return _handle_error(exc)


async def experience_accessibility_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "PATCH":
            body = await request.json()
            return json_response(platform_builder.experience.accessibility(body))
        return json_response(platform_builder.experience.accessibility())
    except Exception as exc:
        return _handle_error(exc)


async def experience_ui_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.experience.ui_dashboard())
    except Exception as exc:
        return _handle_error(exc)


async def experience_session_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            return json_response(platform_builder.experience.start_session(), status=201)
        session_id = request.match_info.get("session_id")
        if not session_id:
            raise ValidationError("session_id is required")
        if request.method == "PATCH":
            body = await request.json()
            return json_response(platform_builder.experience.update_session(session_id, body))
        return json_response(platform_builder.experience.get_session(session_id))
    except Exception as exc:
        return _handle_error(exc)


async def experience_session_summary_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.experience.summary(request.match_info["session_id"]))
    except Exception as exc:
        return _handle_error(exc)


async def experience_create_handler(request: web.Request) -> web.Response:
    try:
        return json_response(
            platform_builder.experience.create(request.match_info["session_id"]),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


# --- Sprint 29.12 — Enterprise Workspace OS / Unified Workspace Platform ---


async def workspace_os_catalog_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.workspace_os.catalog())
    except Exception as exc:
        return _handle_error(exc)


async def workspace_os_status_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.workspace_os.status())
    except Exception as exc:
        return _handle_error(exc)


async def workspace_os_engine_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.workspace_os.engine_overview())
    except Exception as exc:
        return _handle_error(exc)


async def workspace_os_types_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.workspace_os.workspace_types(body.get("type")),
                status=201,
            )
        wtype = request.rel_url.query.get("type")
        return json_response(platform_builder.workspace_os.workspace_types(wtype))
    except Exception as exc:
        return _handle_error(exc)


async def workspace_os_layout_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "PATCH":
            body = await request.json()
            return json_response(platform_builder.workspace_os.layout_engine(body))
        return json_response(platform_builder.workspace_os.layout_engine())
    except Exception as exc:
        return _handle_error(exc)


async def workspace_os_session_mgmt_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "PATCH":
            body = await request.json()
            return json_response(platform_builder.workspace_os.session_management(body))
        return json_response(platform_builder.workspace_os.session_management())
    except Exception as exc:
        return _handle_error(exc)


async def workspace_os_modules_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.workspace_os.module_integration(body.get("module")),
                status=201,
            )
        return json_response(platform_builder.workspace_os.module_integration())
    except Exception as exc:
        return _handle_error(exc)


async def workspace_os_context_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "PATCH":
            body = await request.json()
            return json_response(platform_builder.workspace_os.context_engine(body))
        return json_response(platform_builder.workspace_os.context_engine())
    except Exception as exc:
        return _handle_error(exc)


async def workspace_os_multitasking_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.workspace_os.multitasking(
                    action=body.get("action"),
                    workspace_id=body.get("workspace_id"),
                    name=body.get("name"),
                    workspace_type=body.get("type") or body.get("workspace_type"),
                    clipboard_item=body.get("clipboard_item"),
                    task=body.get("task"),
                ),
                status=201,
            )
        return json_response(platform_builder.workspace_os.multitasking())
    except Exception as exc:
        return _handle_error(exc)


async def workspace_os_search_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.workspace_os.workspace_search(
                    body.get("query"),
                    body.get("scope"),
                ),
                status=201,
            )
        query = request.rel_url.query.get("q") or request.rel_url.query.get("query")
        scope = request.rel_url.query.get("scope")
        return json_response(platform_builder.workspace_os.workspace_search(query, scope))
    except Exception as exc:
        return _handle_error(exc)


async def workspace_os_performance_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.workspace_os.performance(action=body.get("action")),
                status=201,
            )
        return json_response(platform_builder.workspace_os.performance())
    except Exception as exc:
        return _handle_error(exc)


async def workspace_os_ui_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.workspace_os.ui_dashboard())
    except Exception as exc:
        return _handle_error(exc)


async def workspace_os_wizard_session_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            return json_response(platform_builder.workspace_os.start_session(), status=201)
        session_id = request.match_info.get("session_id")
        if not session_id:
            raise ValidationError("session_id is required")
        if request.method == "PATCH":
            body = await request.json()
            return json_response(platform_builder.workspace_os.update_session(session_id, body))
        return json_response(platform_builder.workspace_os.get_session(session_id))
    except Exception as exc:
        return _handle_error(exc)


async def workspace_os_wizard_summary_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.workspace_os.summary(request.match_info["session_id"]))
    except Exception as exc:
        return _handle_error(exc)


async def workspace_os_create_handler(request: web.Request) -> web.Response:
    try:
        return json_response(
            platform_builder.workspace_os.create(request.match_info["session_id"]),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


# --- Sprint 29.13 — Enterprise Command Center OS / Universal Command Platform ---


async def command_center_catalog_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.command_center_os.catalog())
    except Exception as exc:
        return _handle_error(exc)


async def command_center_status_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.command_center_os.status())
    except Exception as exc:
        return _handle_error(exc)


async def command_center_engine_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.command_center_os.engine_overview())
    except Exception as exc:
        return _handle_error(exc)


async def command_center_palette_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.command_center_os.command_palette(body.get("query")),
                status=201,
            )
        query = request.rel_url.query.get("q") or request.rel_url.query.get("query")
        return json_response(platform_builder.command_center_os.command_palette(query))
    except Exception as exc:
        return _handle_error(exc)


async def command_center_execute_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.command_center_os.execute_command(body.get("command_id")),
                status=201,
            )
        return json_response(platform_builder.command_center_os.execute_command())
    except Exception as exc:
        return _handle_error(exc)


async def command_center_categories_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.command_center_os.categories())
    except Exception as exc:
        return _handle_error(exc)


async def command_center_voice_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "PATCH":
            body = await request.json()
            return json_response(platform_builder.command_center_os.voice_foundation(body))
        return json_response(platform_builder.command_center_os.voice_foundation())
    except Exception as exc:
        return _handle_error(exc)


async def command_center_hotkeys_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "PATCH":
            body = await request.json()
            return json_response(platform_builder.command_center_os.hotkey_engine(body))
        return json_response(platform_builder.command_center_os.hotkey_engine())
    except Exception as exc:
        return _handle_error(exc)


async def command_center_history_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.command_center_os.command_history(
                    action=body.get("action"),
                    command_id=body.get("command_id"),
                ),
                status=201,
            )
        return json_response(platform_builder.command_center_os.command_history())
    except Exception as exc:
        return _handle_error(exc)


async def command_center_assistant_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.command_center_os.ai_assistant(
                    utterance=body.get("utterance") or body.get("query"),
                    context=body.get("context"),
                ),
                status=201,
            )
        return json_response(platform_builder.command_center_os.ai_assistant())
    except Exception as exc:
        return _handle_error(exc)


async def command_center_performance_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.command_center_os.performance(action=body.get("action")),
                status=201,
            )
        return json_response(platform_builder.command_center_os.performance())
    except Exception as exc:
        return _handle_error(exc)


async def command_center_ui_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.command_center_os.ui_dashboard())
    except Exception as exc:
        return _handle_error(exc)


async def command_center_wizard_session_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            return json_response(platform_builder.command_center_os.start_session(), status=201)
        session_id = request.match_info.get("session_id")
        if not session_id:
            raise ValidationError("session_id is required")
        if request.method == "PATCH":
            body = await request.json()
            return json_response(
                platform_builder.command_center_os.update_session(session_id, body)
            )
        return json_response(platform_builder.command_center_os.get_session(session_id))
    except Exception as exc:
        return _handle_error(exc)


async def command_center_wizard_summary_handler(request: web.Request) -> web.Response:
    try:
        return json_response(
            platform_builder.command_center_os.summary(request.match_info["session_id"])
        )
    except Exception as exc:
        return _handle_error(exc)


async def command_center_create_handler(request: web.Request) -> web.Response:
    try:
        return json_response(
            platform_builder.command_center_os.create(request.match_info["session_id"]),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


# --- Sprint 29.14 — Navigation Intelligence Engine / Context Navigation Platform ---


async def nav_intel_catalog_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.navigation_intelligence.catalog())
    except Exception as exc:
        return _handle_error(exc)


async def nav_intel_status_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.navigation_intelligence.status())
    except Exception as exc:
        return _handle_error(exc)


async def nav_intel_engine_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.navigation_intelligence.engine_overview())
    except Exception as exc:
        return _handle_error(exc)


async def nav_intel_graph_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.navigation_intelligence.navigation_graph(body.get("graph")),
                status=201,
            )
        graph = request.rel_url.query.get("graph")
        return json_response(platform_builder.navigation_intelligence.navigation_graph(graph))
    except Exception as exc:
        return _handle_error(exc)


async def nav_intel_context_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "PATCH":
            body = await request.json()
            return json_response(platform_builder.navigation_intelligence.context_aware(body))
        return json_response(platform_builder.navigation_intelligence.context_aware())
    except Exception as exc:
        return _handle_error(exc)


async def nav_intel_recommendations_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.navigation_intelligence.smart_recommendations())
    except Exception as exc:
        return _handle_error(exc)


async def nav_intel_history_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.navigation_intelligence.navigation_history(
                    action=body.get("action"),
                    location=body.get("location"),
                    project=body.get("project"),
                    organization=body.get("organization"),
                ),
                status=201,
            )
        return json_response(platform_builder.navigation_intelligence.navigation_history())
    except Exception as exc:
        return _handle_error(exc)


async def nav_intel_quick_access_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "PATCH":
            body = await request.json()
            return json_response(platform_builder.navigation_intelligence.quick_access(body))
        return json_response(platform_builder.navigation_intelligence.quick_access())
    except Exception as exc:
        return _handle_error(exc)


async def nav_intel_cross_platform_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.navigation_intelligence.cross_platform(body.get("target")),
                status=201,
            )
        return json_response(platform_builder.navigation_intelligence.cross_platform())
    except Exception as exc:
        return _handle_error(exc)


async def nav_intel_search_routing_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.navigation_intelligence.search_routing(body.get("query")),
                status=201,
            )
        query = request.rel_url.query.get("q") or request.rel_url.query.get("query")
        return json_response(platform_builder.navigation_intelligence.search_routing(query))
    except Exception as exc:
        return _handle_error(exc)


async def nav_intel_performance_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.navigation_intelligence.performance(action=body.get("action")),
                status=201,
            )
        return json_response(platform_builder.navigation_intelligence.performance())
    except Exception as exc:
        return _handle_error(exc)


async def nav_intel_ui_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.navigation_intelligence.ui_dashboard())
    except Exception as exc:
        return _handle_error(exc)


async def nav_intel_wizard_session_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            return json_response(
                platform_builder.navigation_intelligence.start_session(),
                status=201,
            )
        session_id = request.match_info.get("session_id")
        if not session_id:
            raise ValidationError("session_id is required")
        if request.method == "PATCH":
            body = await request.json()
            return json_response(
                platform_builder.navigation_intelligence.update_session(session_id, body)
            )
        return json_response(platform_builder.navigation_intelligence.get_session(session_id))
    except Exception as exc:
        return _handle_error(exc)


async def nav_intel_wizard_summary_handler(request: web.Request) -> web.Response:
    try:
        return json_response(
            platform_builder.navigation_intelligence.summary(request.match_info["session_id"])
        )
    except Exception as exc:
        return _handle_error(exc)


async def nav_intel_create_handler(request: web.Request) -> web.Response:
    try:
        return json_response(
            platform_builder.navigation_intelligence.create(request.match_info["session_id"]),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


# --- Sprint 29.15 — Workflow Intelligence OS / Global Process Orchestrator ---


async def workflow_intel_catalog_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.workflow_intelligence.catalog())
    except Exception as exc:
        return _handle_error(exc)


async def workflow_intel_status_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.workflow_intelligence.status())
    except Exception as exc:
        return _handle_error(exc)


async def workflow_intel_engine_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.workflow_intelligence.engine_overview())
    except Exception as exc:
        return _handle_error(exc)


async def workflow_intel_graph_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.workflow_intelligence.workflow_graph(body.get("type")),
                status=201,
            )
        graph_type = request.rel_url.query.get("type")
        return json_response(platform_builder.workflow_intelligence.workflow_graph(graph_type))
    except Exception as exc:
        return _handle_error(exc)


async def workflow_intel_dependencies_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.workflow_intelligence.dependency_analysis())
    except Exception as exc:
        return _handle_error(exc)


async def workflow_intel_bottlenecks_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.workflow_intelligence.bottleneck_detection())
    except Exception as exc:
        return _handle_error(exc)


async def workflow_intel_critical_path_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.workflow_intelligence.critical_path())
    except Exception as exc:
        return _handle_error(exc)


async def workflow_intel_resources_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.workflow_intelligence.resource_coordination())
    except Exception as exc:
        return _handle_error(exc)


async def workflow_intel_recommendations_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.workflow_intelligence.workflow_recommendations())
    except Exception as exc:
        return _handle_error(exc)


async def workflow_intel_orchestration_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.workflow_intelligence.enterprise_orchestration(
                    body.get("target")
                ),
                status=201,
            )
        return json_response(platform_builder.workflow_intelligence.enterprise_orchestration())
    except Exception as exc:
        return _handle_error(exc)


async def workflow_intel_performance_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.workflow_intelligence.performance(action=body.get("action")),
                status=201,
            )
        return json_response(platform_builder.workflow_intelligence.performance())
    except Exception as exc:
        return _handle_error(exc)


async def workflow_intel_ui_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.workflow_intelligence.ui_dashboard())
    except Exception as exc:
        return _handle_error(exc)


async def workflow_intel_wizard_session_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            return json_response(
                platform_builder.workflow_intelligence.start_session(),
                status=201,
            )
        session_id = request.match_info.get("session_id")
        if not session_id:
            raise ValidationError("session_id is required")
        if request.method == "PATCH":
            body = await request.json()
            return json_response(
                platform_builder.workflow_intelligence.update_session(session_id, body)
            )
        return json_response(platform_builder.workflow_intelligence.get_session(session_id))
    except Exception as exc:
        return _handle_error(exc)


async def workflow_intel_wizard_summary_handler(request: web.Request) -> web.Response:
    try:
        return json_response(
            platform_builder.workflow_intelligence.summary(request.match_info["session_id"])
        )
    except Exception as exc:
        return _handle_error(exc)


async def workflow_intel_create_handler(request: web.Request) -> web.Response:
    try:
        return json_response(
            platform_builder.workflow_intelligence.create(request.match_info["session_id"]),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


# --- Sprint 29.16 — Enterprise Digital Twin Core / Organization Mirror ---


async def digital_twin_catalog_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.digital_twin.catalog())
    except Exception as exc:
        return _handle_error(exc)


async def digital_twin_status_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.digital_twin.status())
    except Exception as exc:
        return _handle_error(exc)


async def digital_twin_engine_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.digital_twin.engine_overview())
    except Exception as exc:
        return _handle_error(exc)


async def digital_twin_organization_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.digital_twin.organization_mirror())
    except Exception as exc:
        return _handle_error(exc)


async def digital_twin_ai_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.digital_twin.ai_mirror())
    except Exception as exc:
        return _handle_error(exc)


async def digital_twin_workflow_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.digital_twin.workflow_mirror())
    except Exception as exc:
        return _handle_error(exc)


async def digital_twin_knowledge_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.digital_twin.knowledge_mirror())
    except Exception as exc:
        return _handle_error(exc)


async def digital_twin_resources_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.digital_twin.resource_mirror())
    except Exception as exc:
        return _handle_error(exc)


async def digital_twin_snapshots_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.digital_twin.snapshot_engine(
                    action=body.get("action") or "capture",
                    snapshot_type=body.get("type"),
                    label=body.get("label"),
                ),
                status=201,
            )
        return json_response(platform_builder.digital_twin.snapshot_engine())
    except Exception as exc:
        return _handle_error(exc)


async def digital_twin_comparison_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.digital_twin.state_comparison(
                    dimension=body.get("dimension"),
                    from_version=body.get("from_version"),
                    to_version=body.get("to_version"),
                ),
                status=201,
            )
        dimension = request.rel_url.query.get("dimension")
        return json_response(platform_builder.digital_twin.state_comparison(dimension=dimension))
    except Exception as exc:
        return _handle_error(exc)


async def digital_twin_sync_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.digital_twin.sync_engine.sync(mode=body.get("mode")),
                status=201,
            )
        return json_response(platform_builder.digital_twin.sync_engine.status())
    except Exception as exc:
        return _handle_error(exc)


async def digital_twin_performance_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.digital_twin.performance(action=body.get("action")),
                status=201,
            )
        return json_response(platform_builder.digital_twin.performance())
    except Exception as exc:
        return _handle_error(exc)


async def digital_twin_ui_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.digital_twin.ui_dashboard())
    except Exception as exc:
        return _handle_error(exc)


async def digital_twin_wizard_session_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            return json_response(platform_builder.digital_twin.start_session(), status=201)
        session_id = request.match_info.get("session_id")
        if not session_id:
            raise ValidationError("session_id is required")
        if request.method == "PATCH":
            body = await request.json()
            return json_response(platform_builder.digital_twin.update_session(session_id, body))
        return json_response(platform_builder.digital_twin.get_session(session_id))
    except Exception as exc:
        return _handle_error(exc)


async def digital_twin_wizard_summary_handler(request: web.Request) -> web.Response:
    try:
        return json_response(
            platform_builder.digital_twin.summary(request.match_info["session_id"])
        )
    except Exception as exc:
        return _handle_error(exc)


async def digital_twin_create_handler(request: web.Request) -> web.Response:
    try:
        return json_response(
            platform_builder.digital_twin.create(request.match_info["session_id"]),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


# --- Sprint 29.17 — Digital Twin Intelligence / Scenario Analysis ---


async def twin_intelligence_catalog_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.twin_intelligence.catalog())
    except Exception as exc:
        return _handle_error(exc)


async def twin_intelligence_status_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.twin_intelligence.status())
    except Exception as exc:
        return _handle_error(exc)


async def twin_intelligence_engine_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.twin_intelligence.engine_overview())
    except Exception as exc:
        return _handle_error(exc)


async def twin_intelligence_scenarios_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.twin_intelligence.scenario_analysis(
                    action=body.get("action") or "prepare",
                    scenario_type=body.get("type"),
                    label=body.get("label"),
                ),
                status=201,
            )
        return json_response(platform_builder.twin_intelligence.scenario_analysis())
    except Exception as exc:
        return _handle_error(exc)


async def twin_intelligence_what_if_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.twin_intelligence.what_if_engine(
                    action=body.get("action"),
                    input_payload=body.get("input") or body.get("payload"),
                ),
                status=201,
            )
        return json_response(platform_builder.twin_intelligence.what_if_engine())
    except Exception as exc:
        return _handle_error(exc)


async def twin_intelligence_impact_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.twin_intelligence.impact_analysis(dimension=body.get("dimension")),
                status=201,
            )
        dimension = request.rel_url.query.get("dimension")
        return json_response(platform_builder.twin_intelligence.impact_analysis(dimension=dimension))
    except Exception as exc:
        return _handle_error(exc)


async def twin_intelligence_risk_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.twin_intelligence.risk_analysis(category=body.get("category")),
                status=201,
            )
        category = request.rel_url.query.get("category")
        return json_response(platform_builder.twin_intelligence.risk_analysis(category=category))
    except Exception as exc:
        return _handle_error(exc)


async def twin_intelligence_capacity_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.twin_intelligence.capacity_analysis(dimension=body.get("dimension")),
                status=201,
            )
        dimension = request.rel_url.query.get("dimension")
        return json_response(
            platform_builder.twin_intelligence.capacity_analysis(dimension=dimension)
        )
    except Exception as exc:
        return _handle_error(exc)


async def twin_intelligence_recommendations_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.twin_intelligence.recommendations(
                    suggestion_type=body.get("type") or body.get("suggestion_type")
                ),
                status=201,
            )
        suggestion_type = request.rel_url.query.get("type")
        return json_response(
            platform_builder.twin_intelligence.recommendations(suggestion_type=suggestion_type)
        )
    except Exception as exc:
        return _handle_error(exc)


async def twin_intelligence_comparison_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.twin_intelligence.scenario_comparison(
                    mode=body.get("mode"),
                    scenario_a=body.get("scenario_a"),
                    scenario_b=body.get("scenario_b"),
                ),
                status=201,
            )
        mode = request.rel_url.query.get("mode")
        return json_response(platform_builder.twin_intelligence.scenario_comparison(mode=mode))
    except Exception as exc:
        return _handle_error(exc)


async def twin_intelligence_performance_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.twin_intelligence.performance(action=body.get("action")),
                status=201,
            )
        return json_response(platform_builder.twin_intelligence.performance())
    except Exception as exc:
        return _handle_error(exc)


async def twin_intelligence_ui_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.twin_intelligence.ui_dashboard())
    except Exception as exc:
        return _handle_error(exc)


async def twin_intelligence_wizard_session_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            return json_response(platform_builder.twin_intelligence.start_session(), status=201)
        session_id = request.match_info.get("session_id")
        if not session_id:
            raise ValidationError("session_id is required")
        if request.method == "PATCH":
            body = await request.json()
            return json_response(platform_builder.twin_intelligence.update_session(session_id, body))
        return json_response(platform_builder.twin_intelligence.get_session(session_id))
    except Exception as exc:
        return _handle_error(exc)


async def twin_intelligence_wizard_summary_handler(request: web.Request) -> web.Response:
    try:
        return json_response(
            platform_builder.twin_intelligence.summary(request.match_info["session_id"])
        )
    except Exception as exc:
        return _handle_error(exc)


async def twin_intelligence_create_handler(request: web.Request) -> web.Response:
    try:
        return json_response(
            platform_builder.twin_intelligence.create(request.match_info["session_id"]),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


# --- Sprint 29.18 — Enterprise Strategy Engine / Executive Decision Intelligence ---


async def strategy_catalog_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.strategy.catalog())
    except Exception as exc:
        return _handle_error(exc)


async def strategy_status_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.strategy.status())
    except Exception as exc:
        return _handle_error(exc)


async def strategy_engine_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.strategy.engine_overview())
    except Exception as exc:
        return _handle_error(exc)


async def strategy_sources_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.strategy.data_sources(action=body.get("action") or "aggregate"),
                status=201,
            )
        return json_response(platform_builder.strategy.data_sources())
    except Exception as exc:
        return _handle_error(exc)


async def strategy_overview_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.strategy.strategic_overview(surface=body.get("surface")),
                status=201,
            )
        surface = request.rel_url.query.get("surface")
        return json_response(platform_builder.strategy.strategic_overview(surface=surface))
    except Exception as exc:
        return _handle_error(exc)


async def strategy_priorities_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.strategy.strategic_priorities(category=body.get("category")),
                status=201,
            )
        category = request.rel_url.query.get("category")
        return json_response(platform_builder.strategy.strategic_priorities(category=category))
    except Exception as exc:
        return _handle_error(exc)


async def strategy_recommendations_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.strategy.executive_recommendations(
                    recommendation_type=body.get("type") or body.get("recommendation_type")
                ),
                status=201,
            )
        recommendation_type = request.rel_url.query.get("type")
        return json_response(
            platform_builder.strategy.executive_recommendations(
                recommendation_type=recommendation_type
            )
        )
    except Exception as exc:
        return _handle_error(exc)


async def strategy_scorecard_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.strategy.enterprise_scorecard(metric=body.get("metric")),
                status=201,
            )
        metric = request.rel_url.query.get("metric")
        return json_response(platform_builder.strategy.enterprise_scorecard(metric=metric))
    except Exception as exc:
        return _handle_error(exc)


async def strategy_timeline_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.strategy.executive_timeline(segment=body.get("segment")),
                status=201,
            )
        segment = request.rel_url.query.get("segment")
        return json_response(platform_builder.strategy.executive_timeline(segment=segment))
    except Exception as exc:
        return _handle_error(exc)


async def strategy_decisions_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.strategy.decision_support(feature=body.get("feature")),
                status=201,
            )
        feature = request.rel_url.query.get("feature")
        return json_response(platform_builder.strategy.decision_support(feature=feature))
    except Exception as exc:
        return _handle_error(exc)


async def strategy_performance_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            return json_response(
                platform_builder.strategy.performance(action=body.get("action")),
                status=201,
            )
        return json_response(platform_builder.strategy.performance())
    except Exception as exc:
        return _handle_error(exc)


async def strategy_ui_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.strategy.ui_dashboard())
    except Exception as exc:
        return _handle_error(exc)


async def strategy_wizard_session_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            return json_response(platform_builder.strategy.start_session(), status=201)
        session_id = request.match_info.get("session_id")
        if not session_id:
            raise ValidationError("session_id is required")
        if request.method == "PATCH":
            body = await request.json()
            return json_response(platform_builder.strategy.update_session(session_id, body))
        return json_response(platform_builder.strategy.get_session(session_id))
    except Exception as exc:
        return _handle_error(exc)


async def strategy_wizard_summary_handler(request: web.Request) -> web.Response:
    try:
        return json_response(platform_builder.strategy.summary(request.match_info["session_id"]))
    except Exception as exc:
        return _handle_error(exc)


async def strategy_create_handler(request: web.Request) -> web.Response:
    try:
        return json_response(
            platform_builder.strategy.create(request.match_info["session_id"]),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
