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

    # Sprint 28.6 — Builder Academy 2.0 & AI Guide
    app.router.add_get(f"{prefix}/academy/v2/catalog", handlers.academy_v2_catalog_handler)
    app.router.add_post(f"{prefix}/academy/v2/sessions", handlers.academy_v2_session_handler)
    app.router.add_get(f"{prefix}/academy/v2/sessions/{{session_id}}", handlers.academy_v2_session_handler)
    app.router.add_patch(
        f"{prefix}/academy/v2/sessions/{{session_id}}",
        handlers.academy_v2_session_handler,
    )
    app.router.add_get(
        f"{prefix}/academy/v2/sessions/{{session_id}}/summary",
        handlers.academy_v2_summary_handler,
    )
    app.router.add_post(
        f"{prefix}/academy/v2/sessions/{{session_id}}/create",
        handlers.academy_v2_create_handler,
    )
    app.router.add_get(f"{prefix}/academy/v2/levels/{{level}}", handlers.academy_v2_level_handler)
    app.router.add_get(f"{prefix}/academy/v2/help/{{field}}", handlers.academy_v2_help_handler)
    app.router.add_post(f"{prefix}/academy/v2/guide", handlers.academy_v2_guide_handler)
    app.router.add_post(f"{prefix}/academy/v2/guide/ask", handlers.academy_v2_guide_ask_handler)
    app.router.add_get(f"{prefix}/academy/v2/recommendations", handlers.academy_v2_recs_handler)
    app.router.add_post(f"{prefix}/academy/v2/analysis", handlers.academy_v2_analysis_handler)
    app.router.add_get(f"{prefix}/academy/v2/impact/{{option_id}}", handlers.academy_v2_impact_handler)
    app.router.add_get(f"{prefix}/academy/v2/learning", handlers.academy_v2_learning_handler)
    app.router.add_get(f"{prefix}/academy/v2/progress", handlers.academy_v2_progress_handler)


    # Sprint 28.7 — God Mode Expansion / Platform Control Center
    app.router.add_get(f"{prefix}/god-mode/control/catalog", handlers.control_catalog_handler)
    app.router.add_get(f"{prefix}/god-mode/control/status", handlers.control_status_handler)
    app.router.add_get(f"{prefix}/god-mode/control/overview", handlers.control_overview_handler)
    app.router.add_get(f"{prefix}/god-mode/control/search", handlers.control_search_handler)
    app.router.add_get(
        f"{prefix}/god-mode/control/objects/{{object_id}}",
        handlers.control_inspect_handler,
    )
    app.router.add_patch(
        f"{prefix}/god-mode/control/objects/{{object_id}}",
        handlers.control_edit_handler,
    )
    app.router.add_get(f"{prefix}/god-mode/control/registries", handlers.control_registries_handler)
    app.router.add_post(f"{prefix}/god-mode/control/registries", handlers.control_registries_handler)
    app.router.add_get(f"{prefix}/god-mode/control/health", handlers.control_health_handler)
    app.router.add_get(f"{prefix}/god-mode/control/diagnostics", handlers.control_diagnostics_handler)
    app.router.add_get(f"{prefix}/god-mode/control/architecture", handlers.control_architecture_handler)
    app.router.add_get(f"{prefix}/god-mode/control/audit", handlers.control_audit_handler)
    app.router.add_post(f"{prefix}/god-mode/control/rollback", handlers.control_rollback_handler)
    app.router.add_get(f"{prefix}/god-mode/control/explain", handlers.control_explain_handler)
    app.router.add_post(f"{prefix}/god-mode/control/explain", handlers.control_explain_handler)
    app.router.add_post(f"{prefix}/god-mode/control/sessions", handlers.control_session_handler)
    app.router.add_get(
        f"{prefix}/god-mode/control/sessions/{{session_id}}",
        handlers.control_session_handler,
    )
    app.router.add_patch(
        f"{prefix}/god-mode/control/sessions/{{session_id}}",
        handlers.control_session_handler,
    )
    app.router.add_get(
        f"{prefix}/god-mode/control/sessions/{{session_id}}/summary",
        handlers.control_summary_handler,
    )
    app.router.add_post(
        f"{prefix}/god-mode/control/sessions/{{session_id}}/create",
        handlers.control_create_handler,
    )

    # Sprint 28.8 — Collaborative AI / Collective Intelligence
    app.router.add_get(f"{prefix}/collaborative-ai/catalog", handlers.collab_catalog_handler)
    app.router.add_get(f"{prefix}/collaborative-ai/status", handlers.collab_status_handler)
    app.router.add_get(f"{prefix}/collaborative-ai/teams", handlers.collab_teams_handler)
    app.router.add_post(f"{prefix}/collaborative-ai/teams", handlers.collab_teams_handler)
    app.router.add_get(f"{prefix}/collaborative-ai/teams/{{team_id}}", handlers.collab_team_handler)
    app.router.add_post(
        f"{prefix}/collaborative-ai/teams/{{team_id}}/roles",
        handlers.collab_roles_handler,
    )
    app.router.add_post(
        f"{prefix}/collaborative-ai/teams/{{team_id}}/sessions",
        handlers.collab_team_session_handler,
    )
    app.router.add_get(
        f"{prefix}/collaborative-ai/sessions/{{session_id}}/workspace",
        handlers.collab_workspace_handler,
    )
    app.router.add_post(
        f"{prefix}/collaborative-ai/sessions/{{session_id}}/tasks",
        handlers.collab_tasks_handler,
    )
    app.router.add_post(
        f"{prefix}/collaborative-ai/sessions/{{session_id}}/knowledge",
        handlers.collab_knowledge_handler,
    )
    app.router.add_post(
        f"{prefix}/collaborative-ai/sessions/{{session_id}}/decide",
        handlers.collab_decide_handler,
    )
    app.router.add_get(
        f"{prefix}/collaborative-ai/sessions/{{session_id}}/report",
        handlers.collab_report_handler,
    )
    app.router.add_get(
        f"{prefix}/collaborative-ai/sessions/{{session_id}}/performance",
        handlers.collab_performance_handler,
    )
    app.router.add_get(
        f"{prefix}/collaborative-ai/sessions/{{session_id}}/explain",
        handlers.collab_explain_handler,
    )
    app.router.add_post(
        f"{prefix}/collaborative-ai/sessions/{{session_id}}/explain",
        handlers.collab_explain_handler,
    )
    app.router.add_get(f"{prefix}/collaborative-ai/ops-foundation", handlers.collab_ops_handler)
    app.router.add_post(f"{prefix}/collaborative-ai/wizard/sessions", handlers.collab_wizard_handler)
    app.router.add_get(
        f"{prefix}/collaborative-ai/wizard/sessions/{{session_id}}",
        handlers.collab_wizard_handler,
    )
    app.router.add_patch(
        f"{prefix}/collaborative-ai/wizard/sessions/{{session_id}}",
        handlers.collab_wizard_handler,
    )
    app.router.add_get(
        f"{prefix}/collaborative-ai/wizard/sessions/{{session_id}}/summary",
        handlers.collab_wizard_summary_handler,
    )
    app.router.add_post(
        f"{prefix}/collaborative-ai/wizard/sessions/{{session_id}}/create",
        handlers.collab_wizard_create_handler,
    )

    # Sprint 29.1 — Enterprise AI Operations Center
    app.router.add_get(f"{prefix}/operations/catalog", handlers.ops_catalog_handler)
    app.router.add_get(f"{prefix}/operations/status", handlers.ops_status_handler)
    app.router.add_get(f"{prefix}/operations/dashboard", handlers.ops_dashboard_handler)
    app.router.add_get(f"{prefix}/operations/live-status", handlers.ops_live_status_handler)
    app.router.add_get(f"{prefix}/operations/activity", handlers.ops_activity_handler)
    app.router.add_get(f"{prefix}/operations/visual-ids", handlers.ops_visual_ids_handler)
    app.router.add_get(
        f"{prefix}/operations/visual-ids/{{object_id}}",
        handlers.ops_visual_ids_handler,
    )
    app.router.add_get(f"{prefix}/operations/wait-experience", handlers.ops_wait_handler)
    app.router.add_get(f"{prefix}/operations/teams", handlers.ops_teams_handler)
    app.router.add_get(f"{prefix}/operations/health", handlers.ops_health_handler)
    app.router.add_get(f"{prefix}/operations/ai-city", handlers.ops_city_handler)
    app.router.add_get(f"{prefix}/operations/summary-view", handlers.ops_summary_view_handler)
    app.router.add_get(f"{prefix}/operations/visual-layer", handlers.ops_visual_layer_handler)
    app.router.add_post(f"{prefix}/operations/sessions", handlers.ops_session_handler)
    app.router.add_get(f"{prefix}/operations/sessions/{{session_id}}", handlers.ops_session_handler)
    app.router.add_patch(f"{prefix}/operations/sessions/{{session_id}}", handlers.ops_session_handler)
    app.router.add_get(
        f"{prefix}/operations/sessions/{{session_id}}/summary",
        handlers.ops_session_summary_handler,
    )
    app.router.add_post(
        f"{prefix}/operations/sessions/{{session_id}}/create",
        handlers.ops_create_handler,
    )

    # Sprint 29.2 — AI Team Map / Live Organization
    app.router.add_get(f"{prefix}/team-map/catalog", handlers.team_map_catalog_handler)
    app.router.add_get(f"{prefix}/team-map/status", handlers.team_map_status_handler)
    app.router.add_get(f"{prefix}/team-map/map", handlers.team_map_view_handler)
    app.router.add_get(f"{prefix}/team-map/cards", handlers.team_map_cards_handler)
    app.router.add_get(f"{prefix}/team-map/live-status", handlers.team_map_live_status_handler)
    app.router.add_get(f"{prefix}/team-map/workload", handlers.team_map_workload_handler)
    app.router.add_get(f"{prefix}/team-map/relationships", handlers.team_map_relationships_handler)
    app.router.add_get(f"{prefix}/team-map/activity", handlers.team_map_activity_handler)
    app.router.add_post(f"{prefix}/team-map/events/subscribe", handlers.team_map_bus_subscribe_handler)
    app.router.add_get(f"{prefix}/team-map/events/poll", handlers.team_map_bus_poll_handler)
    app.router.add_get(f"{prefix}/team-map/visual-objects", handlers.team_map_visual_objects_handler)
    app.router.add_get(
        f"{prefix}/team-map/visual-objects/{{object_id}}",
        handlers.team_map_visual_objects_handler,
    )
    app.router.add_get(f"{prefix}/team-map/ai-city-apis", handlers.team_map_city_apis_handler)
    app.router.add_post(f"{prefix}/team-map/sessions", handlers.team_map_session_handler)
    app.router.add_get(f"{prefix}/team-map/sessions/{{session_id}}", handlers.team_map_session_handler)
    app.router.add_patch(f"{prefix}/team-map/sessions/{{session_id}}", handlers.team_map_session_handler)
    app.router.add_get(
        f"{prefix}/team-map/sessions/{{session_id}}/summary",
        handlers.team_map_session_summary_handler,
    )
    app.router.add_post(
        f"{prefix}/team-map/sessions/{{session_id}}/create",
        handlers.team_map_create_handler,
    )

    # Sprint 29.3 — Visual Behavior Engine / Animation Framework
    app.router.add_get(f"{prefix}/visual-behavior/catalog", handlers.vb_catalog_handler)
    app.router.add_get(f"{prefix}/visual-behavior/status", handlers.vb_status_handler)
    app.router.add_get(f"{prefix}/visual-behavior/overview", handlers.vb_overview_handler)
    app.router.add_get(f"{prefix}/visual-behavior/behaviors", handlers.vb_behaviors_handler)
    app.router.add_get(f"{prefix}/visual-behavior/transitions", handlers.vb_transitions_handler)
    app.router.add_post(f"{prefix}/visual-behavior/transitions/run", handlers.vb_transition_run_handler)
    app.router.add_get(f"{prefix}/visual-behavior/animations", handlers.vb_animations_handler)
    app.router.add_post(f"{prefix}/visual-behavior/animations/play", handlers.vb_play_animation_handler)
    app.router.add_get(f"{prefix}/visual-behavior/object-types", handlers.vb_object_types_handler)
    app.router.add_get(f"{prefix}/visual-behavior/objects", handlers.vb_objects_handler)
    app.router.add_get(
        f"{prefix}/visual-behavior/objects/{{logical_id}}",
        handlers.vb_objects_handler,
    )
    app.router.add_post(f"{prefix}/visual-behavior/events/subscribe", handlers.vb_subscribe_handler)
    app.router.add_get(f"{prefix}/visual-behavior/events/poll", handlers.vb_poll_handler)
    app.router.add_get(f"{prefix}/visual-behavior/wait-experience", handlers.vb_wait_handler)
    app.router.add_get(f"{prefix}/visual-behavior/performance", handlers.vb_performance_handler)
    app.router.add_get(f"{prefix}/visual-behavior/ai-city-apis", handlers.vb_city_apis_handler)
    app.router.add_post(f"{prefix}/visual-behavior/sessions", handlers.vb_session_handler)
    app.router.add_get(
        f"{prefix}/visual-behavior/sessions/{{session_id}}",
        handlers.vb_session_handler,
    )
    app.router.add_patch(
        f"{prefix}/visual-behavior/sessions/{{session_id}}",
        handlers.vb_session_handler,
    )
    app.router.add_get(
        f"{prefix}/visual-behavior/sessions/{{session_id}}/summary",
        handlers.vb_session_summary_handler,
    )
    app.router.add_post(
        f"{prefix}/visual-behavior/sessions/{{session_id}}/create",
        handlers.vb_create_handler,
    )

    # Sprint 29.4 — Visual Rendering Engine / LOD / Viewport
    app.router.add_get(f"{prefix}/rendering/catalog", handlers.render_catalog_handler)
    app.router.add_get(f"{prefix}/rendering/status", handlers.render_status_handler)
    app.router.add_get(f"{prefix}/rendering/renderer", handlers.render_renderer_handler)
    app.router.add_get(f"{prefix}/rendering/lod", handlers.render_lod_handler)
    app.router.add_get(f"{prefix}/rendering/viewport", handlers.render_viewport_handler)
    app.router.add_get(f"{prefix}/rendering/layers", handlers.render_layers_handler)
    app.router.add_get(f"{prefix}/rendering/priorities", handlers.render_priorities_handler)
    app.router.add_get(f"{prefix}/rendering/animation-optimization", handlers.render_anim_opt_handler)
    app.router.add_get(f"{prefix}/rendering/live-organization", handlers.render_live_org_handler)
    app.router.add_get(f"{prefix}/rendering/ai-city", handlers.render_city_handler)
    app.router.add_get(f"{prefix}/rendering/performance", handlers.render_perf_handler)
    app.router.add_post(f"{prefix}/rendering/sync", handlers.render_sync_handler)
    app.router.add_post(f"{prefix}/rendering/sessions", handlers.render_session_handler)
    app.router.add_get(f"{prefix}/rendering/sessions/{{session_id}}", handlers.render_session_handler)
    app.router.add_patch(f"{prefix}/rendering/sessions/{{session_id}}", handlers.render_session_handler)
    app.router.add_get(
        f"{prefix}/rendering/sessions/{{session_id}}/summary",
        handlers.render_session_summary_handler,
    )
    app.router.add_post(
        f"{prefix}/rendering/sessions/{{session_id}}/create",
        handlers.render_create_handler,
    )

    # Sprint 29.5 — Visual Theme Engine / Branding
    app.router.add_get(f"{prefix}/themes/catalog", handlers.theme_catalog_handler)
    app.router.add_get(f"{prefix}/themes/status", handlers.theme_status_handler)
    app.router.add_get(f"{prefix}/themes/engine", handlers.theme_engine_handler)
    app.router.add_get(f"{prefix}/themes/colors", handlers.theme_colors_handler)
    app.router.add_get(f"{prefix}/themes/branding", handlers.theme_branding_handler)
    app.router.add_post(f"{prefix}/themes/branding", handlers.theme_branding_handler)
    app.router.add_get(f"{prefix}/themes/components", handlers.theme_components_handler)
    app.router.add_get(f"{prefix}/themes/ai-style", handlers.theme_ai_style_handler)
    app.router.add_get(f"{prefix}/themes/animation", handlers.theme_animation_handler)
    app.router.add_get(f"{prefix}/themes/accessibility", handlers.theme_a11y_handler)
    app.router.add_get(f"{prefix}/themes/active", handlers.theme_active_handler)
    app.router.add_post(f"{prefix}/themes/switch", handlers.theme_switch_handler)
    app.router.add_get(f"{prefix}/themes/registry", handlers.theme_registry_handler)
    app.router.add_get(f"{prefix}/themes/ai-city", handlers.theme_city_handler)
    app.router.add_post(f"{prefix}/themes/sessions", handlers.theme_session_handler)
    app.router.add_get(f"{prefix}/themes/sessions/{{session_id}}", handlers.theme_session_handler)
    app.router.add_patch(f"{prefix}/themes/sessions/{{session_id}}", handlers.theme_session_handler)
    app.router.add_get(
        f"{prefix}/themes/sessions/{{session_id}}/summary",
        handlers.theme_session_summary_handler,
    )
    app.router.add_post(
        f"{prefix}/themes/sessions/{{session_id}}/create",
        handlers.theme_create_handler,
    )

    # Sprint 29.6 — Visual Asset Registry / Resource Management
    app.router.add_get(f"{prefix}/assets/catalog", handlers.asset_catalog_handler)
    app.router.add_get(f"{prefix}/assets/status", handlers.asset_status_handler)
    app.router.add_get(f"{prefix}/assets/registry", handlers.asset_registry_handler)
    app.router.add_get(f"{prefix}/assets/categories", handlers.asset_categories_handler)
    app.router.add_get(f"{prefix}/assets/versions", handlers.asset_versions_handler)
    app.router.add_post(f"{prefix}/assets/replace", handlers.asset_replace_handler)
    app.router.add_post(f"{prefix}/assets/rollback", handlers.asset_rollback_handler)
    app.router.add_get(f"{prefix}/assets/optimization", handlers.asset_optimization_handler)
    app.router.add_get(f"{prefix}/assets/avatars", handlers.asset_avatars_handler)
    app.router.add_get(f"{prefix}/assets/branding", handlers.asset_branding_handler)
    app.router.add_get(f"{prefix}/assets/ai-city", handlers.asset_city_handler)
    app.router.add_get(f"{prefix}/assets/search", handlers.asset_search_handler)
    app.router.add_get(f"{prefix}/assets/performance", handlers.asset_performance_handler)
    app.router.add_get(f"{prefix}/assets/browser", handlers.asset_browser_handler)
    app.router.add_get(f"{prefix}/assets/preview/{{asset_id}}", handlers.asset_preview_handler)
    app.router.add_post(f"{prefix}/assets/sessions", handlers.asset_session_handler)
    app.router.add_get(f"{prefix}/assets/sessions/{{session_id}}", handlers.asset_session_handler)
    app.router.add_patch(f"{prefix}/assets/sessions/{{session_id}}", handlers.asset_session_handler)
    app.router.add_get(
        f"{prefix}/assets/sessions/{{session_id}}/summary",
        handlers.asset_session_summary_handler,
    )
    app.router.add_post(
        f"{prefix}/assets/sessions/{{session_id}}/create",
        handlers.asset_create_handler,
    )

    # Sprint 29.7 — Visual Simulation Engine / Live Enterprise Simulation
    app.router.add_get(f"{prefix}/simulation/catalog", handlers.sim_catalog_handler)
    app.router.add_get(f"{prefix}/simulation/status", handlers.sim_status_handler)
    app.router.add_get(f"{prefix}/simulation/engine", handlers.sim_engine_handler)
    app.router.add_get(f"{prefix}/simulation/supported", handlers.sim_supported_handler)
    app.router.add_get(f"{prefix}/simulation/live-organization", handlers.sim_live_org_handler)
    app.router.add_get(f"{prefix}/simulation/collaboration", handlers.sim_collab_handler)
    app.router.add_get(f"{prefix}/simulation/workflow", handlers.sim_workflow_handler)
    app.router.add_get(f"{prefix}/simulation/knowledge", handlers.sim_knowledge_handler)
    app.router.add_get(f"{prefix}/simulation/document", handlers.sim_document_handler)
    app.router.add_get(f"{prefix}/simulation/timeline", handlers.sim_timeline_handler)
    app.router.add_post(f"{prefix}/simulation/timeline", handlers.sim_timeline_handler)
    app.router.add_get(f"{prefix}/simulation/performance", handlers.sim_performance_handler)
    app.router.add_get(f"{prefix}/simulation/ui", handlers.sim_ui_handler)
    app.router.add_post(f"{prefix}/simulation/ingest", handlers.sim_ingest_handler)
    app.router.add_post(f"{prefix}/simulation/emit", handlers.sim_emit_handler)
    app.router.add_post(f"{prefix}/simulation/sessions", handlers.sim_session_handler)
    app.router.add_get(f"{prefix}/simulation/sessions/{{session_id}}", handlers.sim_session_handler)
    app.router.add_patch(f"{prefix}/simulation/sessions/{{session_id}}", handlers.sim_session_handler)
    app.router.add_get(
        f"{prefix}/simulation/sessions/{{session_id}}/summary",
        handlers.sim_session_summary_handler,
    )
    app.router.add_post(
        f"{prefix}/simulation/sessions/{{session_id}}/create",
        handlers.sim_create_handler,
    )

    # Sprint 29.8 — Visual Director Engine / Scene Orchestration
    app.router.add_get(f"{prefix}/director/catalog", handlers.dir_catalog_handler)
    app.router.add_get(f"{prefix}/director/status", handlers.dir_status_handler)
    app.router.add_get(f"{prefix}/director/engine", handlers.dir_engine_handler)
    app.router.add_get(f"{prefix}/director/scenes", handlers.dir_scenes_handler)
    app.router.add_post(f"{prefix}/director/scenes", handlers.dir_scenes_handler)
    app.router.add_post(f"{prefix}/director/scenes/switch", handlers.dir_scene_switch_handler)
    app.router.add_post(f"{prefix}/director/scenes/sync", handlers.dir_scene_sync_handler)
    app.router.add_get(f"{prefix}/director/focus", handlers.dir_focus_handler)
    app.router.add_get(f"{prefix}/director/attention", handlers.dir_attention_handler)
    app.router.add_get(f"{prefix}/director/coordination", handlers.dir_coordination_handler)
    app.router.add_get(f"{prefix}/director/live-organization", handlers.dir_live_org_handler)
    app.router.add_get(f"{prefix}/director/camera", handlers.dir_camera_handler)
    app.router.add_post(f"{prefix}/director/camera", handlers.dir_camera_handler)
    app.router.add_get(f"{prefix}/director/conflicts", handlers.dir_conflicts_handler)
    app.router.add_get(f"{prefix}/director/performance", handlers.dir_performance_handler)
    app.router.add_get(f"{prefix}/director/ui", handlers.dir_ui_handler)
    app.router.add_post(f"{prefix}/director/sessions", handlers.dir_session_handler)
    app.router.add_get(f"{prefix}/director/sessions/{{session_id}}", handlers.dir_session_handler)
    app.router.add_patch(f"{prefix}/director/sessions/{{session_id}}", handlers.dir_session_handler)
    app.router.add_get(
        f"{prefix}/director/sessions/{{session_id}}/summary",
        handlers.dir_session_summary_handler,
    )
    app.router.add_post(
        f"{prefix}/director/sessions/{{session_id}}/create",
        handlers.dir_create_handler,
    )

    # Sprint 29.9 — Visual Story Engine / Enterprise Storytelling
    app.router.add_get(f"{prefix}/story/catalog", handlers.story_catalog_handler)
    app.router.add_get(f"{prefix}/story/status", handlers.story_status_handler)
    app.router.add_get(f"{prefix}/story/engine", handlers.story_engine_handler)
    app.router.add_get(f"{prefix}/story/types", handlers.story_types_handler)
    app.router.add_get(f"{prefix}/story/segments", handlers.story_segments_handler)
    app.router.add_post(f"{prefix}/story/build", handlers.story_build_handler)
    app.router.add_get(f"{prefix}/story/organization", handlers.story_org_handler)
    app.router.add_get(f"{prefix}/story/ai", handlers.story_ai_handler)
    app.router.add_get(f"{prefix}/story/workflow", handlers.story_workflow_handler)
    app.router.add_get(f"{prefix}/story/knowledge", handlers.story_knowledge_handler)
    app.router.add_get(f"{prefix}/story/executive", handlers.story_executive_handler)
    app.router.add_post(f"{prefix}/story/navigate", handlers.story_navigate_handler)
    app.router.add_get(f"{prefix}/story/timeline", handlers.story_timeline_handler)
    app.router.add_get(f"{prefix}/story/milestones", handlers.story_milestones_handler)
    app.router.add_get(f"{prefix}/story/history", handlers.story_history_handler)
    app.router.add_get(f"{prefix}/story/ui", handlers.story_ui_handler)
    app.router.add_post(f"{prefix}/story/sessions", handlers.story_session_handler)
    app.router.add_get(f"{prefix}/story/sessions/{{session_id}}", handlers.story_session_handler)
    app.router.add_patch(f"{prefix}/story/sessions/{{session_id}}", handlers.story_session_handler)
    app.router.add_get(
        f"{prefix}/story/sessions/{{session_id}}/summary",
        handlers.story_session_summary_handler,
    )
    app.router.add_post(
        f"{prefix}/story/sessions/{{session_id}}/create",
        handlers.story_create_handler,
    )

    # Sprint 29.10 — Visual Intelligence Engine / Enterprise Visual Analytics
    app.router.add_get(f"{prefix}/intelligence/catalog", handlers.intel_catalog_handler)
    app.router.add_get(f"{prefix}/intelligence/status", handlers.intel_status_handler)
    app.router.add_get(f"{prefix}/intelligence/engine", handlers.intel_engine_handler)
    app.router.add_get(f"{prefix}/intelligence/patterns", handlers.intel_patterns_handler)
    app.router.add_get(f"{prefix}/intelligence/anomalies", handlers.intel_anomalies_handler)
    app.router.add_get(f"{prefix}/intelligence/recommendations", handlers.intel_recommendations_handler)
    app.router.add_get(f"{prefix}/intelligence/executive", handlers.intel_executive_handler)
    app.router.add_get(f"{prefix}/intelligence/heatmaps", handlers.intel_heatmaps_handler)
    app.router.add_get(f"{prefix}/intelligence/trends", handlers.intel_trends_handler)
    app.router.add_get(f"{prefix}/intelligence/health", handlers.intel_health_handler)
    app.router.add_get(f"{prefix}/intelligence/predictive", handlers.intel_predictive_handler)
    app.router.add_post(f"{prefix}/intelligence/analyze", handlers.intel_analyze_handler)
    app.router.add_get(f"{prefix}/intelligence/ui", handlers.intel_ui_handler)
    app.router.add_post(f"{prefix}/intelligence/sessions", handlers.intel_session_handler)
    app.router.add_get(f"{prefix}/intelligence/sessions/{{session_id}}", handlers.intel_session_handler)
    app.router.add_patch(f"{prefix}/intelligence/sessions/{{session_id}}", handlers.intel_session_handler)
    app.router.add_get(
        f"{prefix}/intelligence/sessions/{{session_id}}/summary",
        handlers.intel_session_summary_handler,
    )
    app.router.add_post(
        f"{prefix}/intelligence/sessions/{{session_id}}/create",
        handlers.intel_create_handler,
    )
