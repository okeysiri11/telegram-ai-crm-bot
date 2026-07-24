"""API Standardization models — Sprint 21.2 / v6.0.0-rc2."""

from __future__ import annotations

API_CATEGORIES = (
    "public",
    "internal",
    "ai",
    "integration",
    "administration",
    "webhook",
    "event",
)

HTTP_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE")

API_VERSIONS = ("v1", "v2", "experimental", "deprecated")

AUTH_MECHANISMS = (
    "oauth2",
    "jwt",
    "api_key",
    "service_token",
    "rbac",
    "multi_tenant_context",
)

WS_CHANNELS = (
    "notifications",
    "workflows",
    "ai",
    "monitoring",
    "events",
    "dashboards",
)

EVENT_REQUIRED_FIELDS = (
    "id",
    "type",
    "source",
    "aggregate",
    "version",
    "payload",
    "timestamp",
    "correlation_id",
)

GATEWAY_TARGETS = ("kong", "traefik", "nginx", "envoy")

STANDARD_REST_RESOURCES = (
    "organizations",
    "users",
    "projects",
    "tasks",
    "workflows",
    "ai",
    "documents",
    "analytics",
)

# Known Hub API prefixes inventory seed
KNOWN_HUB_ENDPOINTS = (
    ("/api/enterprise-hub/v1", "public", "hub"),
    ("/api/enterprise-orch/v1", "public", "orchestrator"),
    ("/api/enterprise-kg/v1", "public", "knowledge_graph"),
    ("/api/enterprise-agents/v1", "ai", "ai_agents"),
    ("/api/enterprise-comms/v1", "public", "communications"),
    ("/api/enterprise-workflow/v1", "public", "workflow"),
    ("/api/enterprise-eip/v1", "integration", "eip"),
    ("/api/enterprise-edp/v1", "public", "edp"),
    ("/api/enterprise-isam/v1", "administration", "isam"),
    ("/api/enterprise-obs/v1", "administration", "observability"),
    ("/api/enterprise-tenancy/v1", "administration", "tenancy"),
    ("/api/enterprise-aop/v1", "ai", "ai_orchestrator"),
    ("/api/enterprise-ats/v1", "ai", "ai_tools"),
    ("/api/enterprise-ekp/v1", "ai", "knowledge_platform"),
    ("/api/enterprise-aios/v1", "ai", "aios"),
    ("/api/enterprise-evp/v1", "event", "event_platform"),
    ("/api/enterprise-sdp/v1", "public", "developer_platform"),
    ("/api/enterprise-edf/v1", "integration", "data_fabric"),
    ("/api/enterprise-edt/v1", "public", "digital_twin"),
    ("/api/enterprise-esi/v1", "ai", "simulation_engine"),
    ("/api/enterprise-epm/v1", "public", "process_mining"),
    ("/api/enterprise-ebc/v1", "public", "business_capabilities"),
    ("/api/enterprise-ecc/v1", "administration", "command_center"),
    ("/internal/enterprise-hub/v1", "internal", "hub_internal"),
    ("/api/v1", "public", "unified_rest"),
    ("/webhooks/v1", "webhook", "webhooks"),
    ("/events/v1", "event", "event_api"),
)

INTEGRATION_TARGETS = (
    "kong",
    "traefik",
    "nginx",
    "envoy",
    "sdk",
    "mobile",
    "web_client",
    "ai_agents",
)
