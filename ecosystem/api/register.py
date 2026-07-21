# Register ecosystem API routes.

from __future__ import annotations

from aiohttp import web

from ecosystem.api import (
    assistant_handlers,
    communication_handlers,
    governance_handlers,
    handlers,
    optimization_handlers,
    workforce_handlers,
)
from ecosystem.api.middleware import ecosystem_auth_middleware
from ecosystem.config import DEFAULT_CONFIG


def register_ecosystem_routes(app: web.Application) -> None:
    prefix = DEFAULT_CONFIG.api_prefix
    app.middlewares.append(ecosystem_auth_middleware)

    # Health
    app.router.add_get(f"{prefix}/health", handlers.health_handler)
    app.router.add_get(f"{prefix}/manifest", handlers.manifest_handler)

    # Identity API
    identity = f"{prefix}/identity"
    app.router.add_post(f"{identity}/auth/register", handlers.register_handler)
    app.router.add_post(f"{identity}/auth/login", handlers.login_handler)
    app.router.add_post(f"{identity}/auth/sso", handlers.sso_login_handler)
    app.router.add_route("*", f"{identity}/profile", handlers.profile_handler)
    app.router.add_get(f"{identity}/devices", handlers.devices_handler)
    app.router.add_get(f"{identity}/sessions/history", handlers.session_history_handler)
    app.router.add_post(f"{identity}/mfa/enroll", handlers.mfa_enroll_handler)

    # Organization API
    org = f"{prefix}/organizations"
    app.router.add_post(org, handlers.create_organization_handler)
    app.router.add_get(org, handlers.list_organizations_handler)
    app.router.add_post(f"{org}/workspaces", handlers.create_workspace_handler)
    app.router.add_post(f"{org}/invitations", handlers.invite_member_handler)
    app.router.add_get(f"{prefix}/roles", handlers.list_roles_handler)

    # Workspace API
    ws = f"{prefix}/workspace"
    app.router.add_get(f"{ws}/dashboard", handlers.dashboard_handler)
    app.router.add_get(f"{ws}/search", handlers.global_search_handler)
    app.router.add_route("*", f"{ws}/favorites", handlers.favorites_handler)
    app.router.add_route("*", f"{ws}/notifications", handlers.notifications_handler)
    app.router.add_get(f"{ws}/quick-actions", handlers.quick_actions_handler)

    # Navigation API
    nav = f"{prefix}/navigation"
    app.router.add_get(nav, handlers.navigation_handler)
    app.router.add_post(f"{nav}/open", handlers.open_application_handler)

    # Legacy assistant endpoint (compat)
    app.router.add_post(f"{prefix}/assistant", assistant_handlers.assistant_invoke_handler)

    # Cross-application shared services
    shared = f"{prefix}/shared"
    app.router.add_route("*", f"{shared}/{{service}}", handlers.shared_services_handler)

    # Sprint 7.2 — Communication, Event Bus, Registry, Sync
    comm = f"{prefix}/communication"
    app.router.add_get(f"{comm}/metrics", communication_handlers.communication_metrics_handler)
    app.router.add_post(f"{comm}/messages", communication_handlers.send_message_handler)
    app.router.add_post(f"{comm}/request", communication_handlers.request_response_handler)
    app.router.add_post(f"{comm}/broadcast", communication_handlers.broadcast_handler)
    app.router.add_post(f"{comm}/commands", communication_handlers.command_handler)
    app.router.add_post(f"{comm}/queries", communication_handlers.query_handler)
    app.router.add_post(f"{comm}/acknowledge", communication_handlers.acknowledge_handler)
    app.router.add_get(f"{comm}/dead-letters", communication_handlers.dead_letters_handler)
    app.router.add_post(f"{comm}/subscribe", communication_handlers.subscribe_handler)
    app.router.add_get(f"{comm}/subscriptions", communication_handlers.list_subscriptions_handler)
    app.router.add_post(f"{comm}/context", communication_handlers.share_context_handler)
    app.router.add_post(f"{comm}/agents/delegate", communication_handlers.delegate_agent_handler)

    events = f"{prefix}/events"
    app.router.add_post(events, communication_handlers.publish_event_handler)
    app.router.add_get(events, communication_handlers.list_events_handler)
    app.router.add_get(f"{events}/replay", communication_handlers.replay_events_handler)

    registry = f"{prefix}/registry"
    app.router.add_post(registry, communication_handlers.register_application_handler)
    app.router.add_get(registry, communication_handlers.list_registry_handler)
    app.router.add_get(f"{registry}/health", communication_handlers.registry_health_handler)
    app.router.add_get(f"{registry}/dependencies", communication_handlers.dependency_graph_handler)
    app.router.add_get(f"{registry}/capabilities/{{capability}}", communication_handlers.discover_capability_handler)

    sync = f"{prefix}/sync"
    app.router.add_post(sync, communication_handlers.sync_handler)
    app.router.add_get(f"{sync}/history", communication_handlers.sync_history_handler)

    # Sprint 7.3 — Unified AI Assistant & Global Knowledge
    assistant = f"{prefix}/assistant"
    app.router.add_get(f"{assistant}/metrics", assistant_handlers.assistant_metrics_handler)
    app.router.add_post(f"{assistant}/invoke", assistant_handlers.assistant_invoke_handler)
    app.router.add_post(f"{assistant}/orchestrate", assistant_handlers.assistant_orchestrate_handler)
    app.router.add_get(f"{assistant}/memory", assistant_handlers.memory_recall_handler)

    knowledge = f"{prefix}/knowledge"
    app.router.add_post(knowledge, assistant_handlers.knowledge_upsert_handler)
    app.router.add_get(f"{knowledge}/search", assistant_handlers.knowledge_search_handler)
    app.router.add_post(f"{knowledge}/link", assistant_handlers.knowledge_link_handler)
    app.router.add_post(f"{knowledge}/sync", assistant_handlers.knowledge_sync_handler)

    conversations = f"{prefix}/conversations"
    app.router.add_post(conversations, assistant_handlers.conversation_create_handler)
    app.router.add_get(conversations, assistant_handlers.conversation_list_handler)
    app.router.add_get(f"{conversations}/{{conversation_id}}", assistant_handlers.conversation_get_handler)
    app.router.add_post(f"{conversations}/{{conversation_id}}/summarize", assistant_handlers.conversation_summarize_handler)
    app.router.add_post(f"{conversations}/{{conversation_id}}/restore", assistant_handlers.conversation_restore_handler)

    skills = f"{prefix}/skills"
    app.router.add_get(skills, assistant_handlers.skills_list_handler)
    app.router.add_post(skills, assistant_handlers.skills_register_handler)
    app.router.add_post(f"{skills}/execute", assistant_handlers.skills_execute_handler)

    ctx = f"{prefix}/context"
    app.router.add_get(ctx, assistant_handlers.context_get_handler)
    app.router.add_post(ctx, assistant_handlers.context_update_handler)

    # Sprint 7.4 — Autonomous AI Workforce
    wf = f"{prefix}/workforce"
    app.router.add_get(f"{wf}/metrics", workforce_handlers.workforce_metrics_handler)
    app.router.add_get(f"{wf}/org-chart", workforce_handlers.org_chart_handler)
    app.router.add_get(f"{wf}/specialists", workforce_handlers.list_specialists_handler)
    app.router.add_get(f"{wf}/tasks", workforce_handlers.list_tasks_handler)
    app.router.add_post(f"{wf}/delegate", workforce_handlers.delegate_task_handler)
    app.router.add_post(f"{wf}/tasks/{{task_id}}/execute", workforce_handlers.execute_task_handler)
    app.router.add_post(f"{wf}/run", workforce_handlers.run_workflow_handler)
    app.router.add_post(f"{wf}/escalate", workforce_handlers.escalate_handler)
    app.router.add_get(f"{wf}/balance", workforce_handlers.balance_handler)
    app.router.add_post(f"{wf}/collaborate", workforce_handlers.collaborate_handler)

    executive = f"{prefix}/executive"
    app.router.add_get(executive, workforce_handlers.list_executives_handler)
    app.router.add_post(f"{executive}/decide", workforce_handlers.executive_decide_handler)
    app.router.add_post(f"{executive}/support", workforce_handlers.executive_support_handler)

    departments = f"{prefix}/departments"
    app.router.add_get(departments, workforce_handlers.list_departments_handler)
    app.router.add_get(f"{departments}/{{department_type}}", workforce_handlers.department_roster_handler)

    planning = f"{prefix}/planning"
    app.router.add_post(f"{planning}/objectives", workforce_handlers.create_objective_handler)
    app.router.add_post(f"{planning}/objectives/{{objective_id}}/progress", workforce_handlers.update_objective_handler)
    app.router.add_post(f"{planning}/plans", workforce_handlers.create_plan_handler)
    app.router.add_get(f"{planning}/performance", workforce_handlers.performance_handler)

    governance = f"{prefix}/governance"
    app.router.add_get(governance, workforce_handlers.governance_audit_handler)

    # Sprint 7.6 — Platform Governance, Compliance & Lifecycle
    # Note: exact GET /governance remains workforce audit; platform routes use subpaths.
    app.router.add_get(f"{governance}/metrics", governance_handlers.governance_metrics_handler)
    app.router.add_post(f"{governance}/cycle", governance_handlers.governance_cycle_handler)
    app.router.add_get(f"{governance}/policies", governance_handlers.list_policies_handler)
    app.router.add_post(f"{governance}/policies", governance_handlers.create_policy_handler)
    app.router.add_patch(f"{governance}/policies/{{policy_id}}", governance_handlers.update_policy_handler)
    app.router.add_get(f"{governance}/audit", governance_handlers.audit_trail_handler)
    app.router.add_get(f"{governance}/catalog", governance_handlers.catalog_list_handler)
    app.router.add_post(f"{governance}/catalog", governance_handlers.catalog_register_handler)

    compliance = f"{prefix}/compliance"
    app.router.add_post(f"{compliance}/evaluate", governance_handlers.compliance_evaluate_handler)
    app.router.add_post(f"{compliance}/audit", governance_handlers.compliance_audit_handler)
    app.router.add_get(compliance, governance_handlers.compliance_list_handler)
    app.router.add_post(f"{compliance}/access-reviews", governance_handlers.access_review_handler)

    lifecycle = f"{prefix}/lifecycle"
    app.router.add_post(lifecycle, governance_handlers.lifecycle_register_handler)
    app.router.add_get(lifecycle, governance_handlers.lifecycle_list_handler)
    app.router.add_post(f"{lifecycle}/{{record_id}}/transition", governance_handlers.lifecycle_transition_handler)

    administration = f"{prefix}/administration"
    app.router.add_get(administration, governance_handlers.admin_overview_handler)
    app.router.add_post(f"{administration}/licenses", governance_handlers.admin_license_handler)
    app.router.add_route("*", f"{administration}/flags", governance_handlers.admin_flags_handler)

    risk = f"{prefix}/risk"
    app.router.add_post(risk, governance_handlers.risk_assess_handler)
    app.router.add_get(risk, governance_handlers.risk_list_handler)

    # Sprint 7.5 — Continuous Learning & Optimization
    opt = f"{prefix}/optimization"
    app.router.add_get(f"{opt}/metrics", optimization_handlers.optimization_metrics_handler)
    app.router.add_post(opt, optimization_handlers.optimize_handler)
    app.router.add_get(f"{opt}/benchmarks", optimization_handlers.benchmark_handler)

    learning = f"{prefix}/learning"
    app.router.add_post(f"{learning}/cycles", optimization_handlers.learning_cycle_handler)
    app.router.add_get(f"{learning}/history", optimization_handlers.learning_history_handler)
    app.router.add_post(f"{learning}/executions", optimization_handlers.record_execution_handler)
    app.router.add_post(f"{learning}/decisions", optimization_handlers.track_decision_handler)
    app.router.add_post(f"{learning}/feedback", optimization_handlers.feedback_handler)

    sim = f"{prefix}/simulation"
    app.router.add_post(sim, optimization_handlers.simulation_handler)
    app.router.add_get(sim, optimization_handlers.list_simulations_handler)

    recs = f"{prefix}/recommendations"
    app.router.add_post(recs, optimization_handlers.recommendations_generate_handler)
    app.router.add_get(recs, optimization_handlers.recommendations_list_handler)

    perf = f"{prefix}/performance"
    app.router.add_post(f"{perf}/collect", optimization_handlers.performance_collect_handler)
    app.router.add_get(perf, optimization_handlers.performance_dashboard_handler)
    app.router.add_post(perf, optimization_handlers.performance_record_handler)

    strategy = f"{prefix}/strategy"
    app.router.add_post(strategy, optimization_handlers.strategy_update_handler)
    app.router.add_get(strategy, optimization_handlers.strategy_list_handler)
