"""Register Platform Builder routes — Sprint 28.1."""

from __future__ import annotations

from aiohttp import web

from applications.platform_builder.api import handlers
from applications.platform_builder.api.middleware import auth_middleware
from applications.platform_builder.config import DEFAULT_CONFIG


def register_platform_builder_routes(app: web.Application) -> None:
    prefix = DEFAULT_CONFIG.api_prefix
    if auth_middleware not in app.middlewares:
        app.middlewares.append(auth_middleware)

    app.router.add_get(f"{prefix}/health", handlers.health_handler)
    app.router.add_post(f"{prefix}/bootstrap", handlers.bootstrap_handler)
    app.router.add_get(f"{prefix}/inventory", handlers.inventory_handler)
    app.router.add_get(f"{prefix}/dashboard", handlers.dashboard_handler)
    app.router.add_get(f"{prefix}/builders", handlers.builders_handler)
    app.router.add_get(f"{prefix}/builders/{{builder_id}}", handlers.builder_detail_handler)
    app.router.add_post(f"{prefix}/builders/{{builder_id}}/preview", handlers.builder_preview_handler)
    app.router.add_post(f"{prefix}/builders/{{builder_id}}/create", handlers.builder_create_handler)
    app.router.add_get(f"{prefix}/academy", handlers.academy_handler)
    app.router.add_post(f"{prefix}/academy", handlers.academy_handler)
    app.router.add_get(f"{prefix}/academy/{{builder_id}}/guide", handlers.academy_guide_handler)
    app.router.add_get(f"{prefix}/help/{{builder_id}}", handlers.help_handler)
    app.router.add_get(f"{prefix}/menu", handlers.menu_handler)
    app.router.add_get(f"{prefix}/roles", handlers.roles_handler)
    app.router.add_get(f"{prefix}/god-mode", handlers.god_mode_handler)
    app.router.add_post(f"{prefix}/god-mode/action", handlers.god_mode_action_handler)

    # Sprint 28.2 — Enterprise AI Builder
    app.router.add_get(f"{prefix}/ai-builder/catalog", handlers.ai_catalog_handler)
    app.router.add_post(f"{prefix}/ai-builder/sessions", handlers.ai_session_handler)
    app.router.add_get(f"{prefix}/ai-builder/sessions/{{session_id}}", handlers.ai_session_handler)
    app.router.add_patch(f"{prefix}/ai-builder/sessions/{{session_id}}", handlers.ai_session_handler)
    app.router.add_get(f"{prefix}/ai-builder/names", handlers.ai_names_handler)
    app.router.add_get(
        f"{prefix}/ai-builder/specializations/{{profession_id}}",
        handlers.ai_specializations_handler,
    )
    app.router.add_post(
        f"{prefix}/ai-builder/personality-preview",
        handlers.ai_personality_preview_handler,
    )
    app.router.add_get(
        f"{prefix}/ai-builder/sessions/{{session_id}}/summary",
        handlers.ai_summary_handler,
    )
    app.router.add_post(
        f"{prefix}/ai-builder/sessions/{{session_id}}/create",
        handlers.ai_create_handler,
    )
    app.router.add_get(f"{prefix}/ai-builder/registry", handlers.ai_registry_handler)
    app.router.add_get(f"{prefix}/ai-builder/group-chat", handlers.ai_group_chat_handler)

    # Sprint 28.3 — Enterprise AI Concierge
    app.router.add_get(f"{prefix}/concierge/catalog", handlers.concierge_catalog_handler)
    app.router.add_post(f"{prefix}/concierge/sessions", handlers.concierge_session_handler)
    app.router.add_get(f"{prefix}/concierge/sessions/{{session_id}}", handlers.concierge_session_handler)
    app.router.add_patch(f"{prefix}/concierge/sessions/{{session_id}}", handlers.concierge_session_handler)
    app.router.add_post(f"{prefix}/concierge/preview", handlers.concierge_preview_handler)
    app.router.add_get(
        f"{prefix}/concierge/sessions/{{session_id}}/summary",
        handlers.concierge_summary_handler,
    )
    app.router.add_post(
        f"{prefix}/concierge/sessions/{{session_id}}/create",
        handlers.concierge_create_handler,
    )
    app.router.add_get(f"{prefix}/concierge/registry", handlers.concierge_registry_handler)
    app.router.add_get(
        f"{prefix}/concierge/organizations/{{organization_id}}",
        handlers.concierge_org_handler,
    )

    # Sprint 28.3 — AI Team Center
    app.router.add_get(f"{prefix}/ai-team/status", handlers.ai_team_status_handler)
    app.router.add_get(f"{prefix}/ai-team/dashboard", handlers.ai_team_dashboard_handler)
    app.router.add_get(
        f"{prefix}/ai-team/organizations/{{organization_id}}/dashboard",
        handlers.ai_team_dashboard_handler,
    )
    app.router.add_post(
        f"{prefix}/ai-team/organizations/{{organization_id}}/actions",
        handlers.ai_team_action_handler,
    )
    app.router.add_get(f"{prefix}/ai-team/group-chat", handlers.ai_team_group_chat_handler)

    # Sprint 28.4 — Enterprise Vertical Builder
    app.router.add_get(f"{prefix}/vertical/catalog", handlers.vertical_catalog_handler)
    app.router.add_post(f"{prefix}/vertical/sessions", handlers.vertical_session_handler)
    app.router.add_get(f"{prefix}/vertical/sessions/{{session_id}}", handlers.vertical_session_handler)
    app.router.add_patch(f"{prefix}/vertical/sessions/{{session_id}}", handlers.vertical_session_handler)
    app.router.add_get(
        f"{prefix}/vertical/sessions/{{session_id}}/preview",
        handlers.vertical_preview_handler,
    )
    app.router.add_get(
        f"{prefix}/vertical/sessions/{{session_id}}/summary",
        handlers.vertical_summary_handler,
    )
    app.router.add_post(
        f"{prefix}/vertical/sessions/{{session_id}}/create",
        handlers.vertical_create_handler,
    )
    app.router.add_get(f"{prefix}/vertical/registry", handlers.vertical_registry_handler)

    # Sprint 28.5 — Universal Builder Framework
    app.router.add_get(f"{prefix}/ubf/catalog", handlers.ubf_catalog_handler)
    app.router.add_post(f"{prefix}/ubf/bootstrap", handlers.ubf_bootstrap_handler)
    app.router.add_post(f"{prefix}/ubf/sessions", handlers.ubf_session_handler)
    app.router.add_get(f"{prefix}/ubf/sessions/{{session_id}}", handlers.ubf_session_handler)
    app.router.add_patch(f"{prefix}/ubf/sessions/{{session_id}}", handlers.ubf_session_handler)
    app.router.add_post(
        f"{prefix}/ubf/sessions/{{session_id}}/validate",
        handlers.ubf_validate_handler,
    )
    app.router.add_get(
        f"{prefix}/ubf/sessions/{{session_id}}/preview",
        handlers.ubf_preview_handler,
    )
    app.router.add_get(
        f"{prefix}/ubf/sessions/{{session_id}}/summary",
        handlers.ubf_summary_handler,
    )
    app.router.add_post(
        f"{prefix}/ubf/sessions/{{session_id}}/create",
        handlers.ubf_create_handler,
    )
    app.router.add_get(f"{prefix}/ubf/registry", handlers.ubf_registry_handler)
    app.router.add_get(f"{prefix}/ubf/templates", handlers.ubf_templates_handler)
    app.router.add_post(f"{prefix}/ubf/templates", handlers.ubf_templates_handler)
    app.router.add_post(
        f"{prefix}/ubf/templates/{{template_id}}/clone",
        handlers.ubf_template_clone_handler,
    )
    app.router.add_get(f"{prefix}/ubf/sdk", handlers.ubf_sdk_handler)
    app.router.add_post(f"{prefix}/ubf/sdk/define", handlers.ubf_sdk_define_handler)
