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
