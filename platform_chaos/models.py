"""Chaos Engineering constants — Sprint 25.3."""

from __future__ import annotations

FAILURE_TYPES = (
    "postgresql_offline",
    "redis_offline",
    "event_bus_offline",
    "ai_provider_offline",
    "object_storage_offline",
    "scheduler_failure",
    "authentication_failure",
    "network_latency",
    "packet_loss",
    "high_cpu",
    "memory_exhaustion",
    "disk_full",
    "api_timeout",
    "service_crash",
    "container_restart",
)

CIRCUIT_STATES = ("open", "half_open", "closed")

RETRY_STRATEGIES = (
    "fixed_delay",
    "exponential_backoff",
    "linear_retry",
    "immediate_retry",
)

FALLBACK_TARGETS = (
    "backup_ai_provider",
    "backup_queue",
    "backup_storage",
    "backup_api",
    "local_cache",
    "degraded_mode",
)

DEPENDENCY_CHAIN = (
    "enterprise_hub",
    "api_gateway",
    "workflow_engine",
    "ai_orchestrator",
    "knowledge_graph",
    "event_bus",
    "database",
    "external_providers",
)

REPORT_FORMATS = ("html", "json", "incident_timeline", "recovery_timeline", "root_cause", "recommendations")

INTEGRATION_TARGETS = (
    "enterprise_hub",
    "enterprise_ai_orchestrator",
    "workflow",
    "event_platform",
    "enterprise_knowledge_graph",
    "performance_testing",
    "observability",
    "communications",
)

KPI_TARGETS = {
    "auto_failure_injection": True,
    "auto_recovery_validation": True,
    "retry_fallback_circuit_verified": True,
    "recovery_time_measured": True,
    "incident_history": True,
    "fault_tolerance_reports": True,
    "required_before_production": True,
}

PRINCIPLES = (
    "simulate_never_destroy_data",
    "auto_recovery_checks",
    "ci_cd_fault_tolerance_gate",
    "full_incident_history",
    "no_duplicated_business_logic",
)
