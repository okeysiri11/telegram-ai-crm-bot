"""Register Enterprise Hub routes (Sprint 19.0)."""

from __future__ import annotations

from aiohttp import web

from applications.enterprise_hub.api import handlers, kg_handlers, orch_handlers
from applications.enterprise_hub.api.middleware import auth_middleware
from applications.enterprise_hub.config import DEFAULT_CONFIG


def register_enterprise_hub_routes(app: web.Application) -> None:
    prefix = DEFAULT_CONFIG.api_prefix
    if auth_middleware not in app.middlewares:
        app.middlewares.append(auth_middleware)

    app.router.add_get(f"{prefix}/health", handlers.health_handler)
    app.router.add_post(f"{prefix}/bootstrap", handlers.bootstrap_handler)
    app.router.add_get(f"{prefix}/registry", handlers.registry_handler)
    app.router.add_post(f"{prefix}/registry", handlers.registry_handler)
    app.router.add_get(f"{prefix}/integration", handlers.integration_handler)
    app.router.add_post(f"{prefix}/integration", handlers.integration_handler)
    app.router.add_get(f"{prefix}/identity", handlers.identity_handler)
    app.router.add_post(f"{prefix}/identity", handlers.identity_handler)
    app.router.add_get(f"{prefix}/configuration", handlers.configuration_handler)
    app.router.add_post(f"{prefix}/configuration", handlers.configuration_handler)
    app.router.add_get(f"{prefix}/events", handlers.events_handler)
    app.router.add_post(f"{prefix}/events", handlers.events_handler)
    app.router.add_get(f"{prefix}/dashboard", handlers.dashboard_handler)
    app.router.add_post(f"{prefix}/dashboard", handlers.dashboard_handler)
    app.router.add_get(f"{prefix}/knowledge", handlers.knowledge_handler)
    app.router.add_post(f"{prefix}/knowledge", handlers.knowledge_handler)

    # Sprint 19.1 — AI Orchestrator (additive; prior routes unchanged)
    orch = DEFAULT_CONFIG.orchestrator_api_prefix
    app.router.add_get(f"{orch}/health", orch_handlers.orch_health_handler)
    app.router.add_post(f"{orch}/bootstrap", orch_handlers.orch_bootstrap_handler)
    app.router.add_get(f"{orch}/core", orch_handlers.orch_core_handler)
    app.router.add_post(f"{orch}/core", orch_handlers.orch_core_handler)
    app.router.add_get(f"{orch}/intent", orch_handlers.orch_intent_handler)
    app.router.add_post(f"{orch}/intent", orch_handlers.orch_intent_handler)
    app.router.add_get(f"{orch}/workflow", orch_handlers.orch_workflow_handler)
    app.router.add_post(f"{orch}/workflow", orch_handlers.orch_workflow_handler)
    app.router.add_get(f"{orch}/routing", orch_handlers.orch_routing_handler)
    app.router.add_post(f"{orch}/routing", orch_handlers.orch_routing_handler)
    app.router.add_get(f"{orch}/decisions", orch_handlers.orch_decisions_handler)
    app.router.add_post(f"{orch}/decisions", orch_handlers.orch_decisions_handler)
    app.router.add_get(f"{orch}/monitoring", orch_handlers.orch_monitoring_handler)
    app.router.add_post(f"{orch}/monitoring", orch_handlers.orch_monitoring_handler)
    app.router.add_get(f"{orch}/explain", orch_handlers.orch_explain_handler)
    app.router.add_post(f"{orch}/explain", orch_handlers.orch_explain_handler)
    app.router.add_get(f"{orch}/dashboard", orch_handlers.orch_dashboard_handler)
    app.router.add_post(f"{orch}/dashboard", orch_handlers.orch_dashboard_handler)
    app.router.add_get(f"{orch}/knowledge", orch_handlers.orch_knowledge_handler)
    app.router.add_post(f"{orch}/knowledge", orch_handlers.orch_knowledge_handler)

    # Sprint 19.2 — Unified Knowledge Graph (additive; prior routes unchanged)
    kg = DEFAULT_CONFIG.knowledge_graph_api_prefix
    app.router.add_get(f"{kg}/health", kg_handlers.kg_health_handler)
    app.router.add_post(f"{kg}/bootstrap", kg_handlers.kg_bootstrap_handler)
    app.router.add_get(f"{kg}/graph", kg_handlers.kg_graph_handler)
    app.router.add_post(f"{kg}/graph", kg_handlers.kg_graph_handler)
    app.router.add_get(f"{kg}/memory", kg_handlers.kg_memory_handler)
    app.router.add_post(f"{kg}/memory", kg_handlers.kg_memory_handler)
    app.router.add_get(f"{kg}/semantic", kg_handlers.kg_semantic_handler)
    app.router.add_post(f"{kg}/semantic", kg_handlers.kg_semantic_handler)
    app.router.add_get(f"{kg}/context", kg_handlers.kg_context_handler)
    app.router.add_post(f"{kg}/context", kg_handlers.kg_context_handler)
    app.router.add_get(f"{kg}/ai", kg_handlers.kg_ai_handler)
    app.router.add_post(f"{kg}/ai", kg_handlers.kg_ai_handler)
    app.router.add_get(f"{kg}/sync", kg_handlers.kg_sync_handler)
    app.router.add_post(f"{kg}/sync", kg_handlers.kg_sync_handler)
    app.router.add_get(f"{kg}/dashboard", kg_handlers.kg_dashboard_handler)
    app.router.add_post(f"{kg}/dashboard", kg_handlers.kg_dashboard_handler)
    app.router.add_get(f"{kg}/meta", kg_handlers.kg_meta_handler)
    app.router.add_post(f"{kg}/meta", kg_handlers.kg_meta_handler)
