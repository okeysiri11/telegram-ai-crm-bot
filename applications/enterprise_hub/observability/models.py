"""Observability models and constants — Sprint 19.9."""

from __future__ import annotations

METRIC_KINDS = (
    "cpu",
    "ram",
    "disk",
    "network",
    "database",
    "queue",
    "api",
    "ai_tokens",
    "ai_cost",
    "active_users",
    "active_sessions",
)

LOG_KINDS = (
    "application",
    "audit",
    "ai",
    "integration",
    "security",
    "error",
)

ALERT_LEVELS = ("info", "warning", "error", "critical")

ALERT_CHANNELS = ("telegram", "email", "push", "sms", "webhook")

SERVICE_KINDS = (
    "microservice",
    "ai_agent",
    "integration",
    "queue",
    "background",
)

COLLECTORS = ("system", "application", "ai_agents", "database", "network", "integrations")
EXPORTERS = ("prometheus", "grafana", "elastic", "loki", "otel")
DASHBOARD_KINDS = ("platform", "infrastructure", "ai", "integrations", "business")
INCIDENT_STATUSES = ("open", "investigating", "mitigated", "resolved")
