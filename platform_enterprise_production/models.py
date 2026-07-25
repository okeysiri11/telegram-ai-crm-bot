"""Production Readiness constants — Sprint 25.6."""

from __future__ import annotations

HEALTH_TARGETS = (
    "api_gateway",
    "enterprise_hub",
    "ai_orchestrator",
    "knowledge_graph",
    "workflow_engine",
    "event_bus",
    "postgresql",
    "redis",
    "object_storage",
    "notification_center",
    "scheduler",
    "marketplace",
    "ai_provider_hub",
)

MONITORING_SIGNALS = (
    "cpu",
    "memory",
    "disk",
    "network",
    "database",
    "cache",
    "queue",
    "ai_providers",
    "active_sessions",
    "api_requests",
    "background_jobs",
)

METRIC_KINDS = (
    "requests_per_sec",
    "response_time",
    "error_rate",
    "queue_size",
    "active_users",
    "active_companies",
    "ai_requests",
    "workflow_executions",
    "database_connections",
)

LOG_STREAMS = (
    "application",
    "api",
    "security",
    "workflow",
    "ai",
    "database",
    "audit",
    "system",
)

LOG_CAPABILITIES = ("search", "filter", "export", "archive")

ALERT_TRIGGERS = (
    "service_failure",
    "cpu_exceeded",
    "memory_shortage",
    "api_errors",
    "database_failure",
    "ai_provider_unavailable",
    "workflow_failure",
    "critical_security_event",
)

SCALING_MODES = (
    "horizontal_scaling",
    "vertical_scaling",
    "auto_scaling_rules",
    "resource_thresholds",
    "capacity_planning",
)

DEPLOYMENT_CHECKS = (
    "migrations",
    "backups",
    "version_compatibility",
    "tests",
    "security",
    "performance",
    "fault_tolerance",
)

DASHBOARD_SECTIONS = (
    "system_health",
    "active_services",
    "infrastructure",
    "monitoring",
    "alerts",
    "logs",
    "metrics",
    "deployments",
    "capacity",
    "availability",
)

REPORT_KINDS = (
    "production",
    "health",
    "monitoring",
    "capacity",
    "availability",
    "deployment",
)

INTEGRATION_TARGETS = (
    "enterprise_hub",
    "security_verification",
    "migration",
    "chaos_engineering",
    "performance_testing",
    "observability",
    "communications",
    "test_infrastructure",
)

KPI_TARGETS = {
    "unified_production_platform": True,
    "continuous_monitoring": True,
    "centralized_logs": True,
    "automatic_health_checks": True,
    "intelligent_alerts": True,
    "scaling_ready": True,
    "cloud_deployment_ready": True,
    "block_release_when_not_ready": True,
    "no_duplicated_obs_logic": True,
    "no_duplicated_epr_logic": True,
}

PRINCIPLES = (
    "continuous_health_checks",
    "centralized_production_control",
    "block_release_when_not_ready",
    "additive_to_obs_epf_epr",
    "integrates_security_migration_chaos_perf",
    "no_duplicated_business_logic",
    "cloud_ready",
)

SERVICE_FIELDS = (
    "service_id",
    "name",
    "version",
    "status",
    "environment",
    "health",
    "uptime",
    "last_deployment",
    "current_load",
    "availability",
)
