"""Performance Testing constants — Sprint 25.2."""

from __future__ import annotations

LOAD_USER_LEVELS = (10, 50, 100, 250, 500, 1000, 5000)

SOAK_DURATIONS_HOURS = (1, 6, 12, 24)

STRESS_LIMITS = ("api", "database", "queues", "ai_hub", "event_bus")

RESOURCE_METRICS = (
    "cpu",
    "ram",
    "disk",
    "network",
    "database",
    "redis",
    "event_bus",
    "ai_providers",
)

ADVICE_KINDS = (
    "add_index",
    "optimize_sql",
    "increase_connection_pool",
    "change_caching",
    "optimize_api",
    "split_service",
    "scale_module",
)

INTEGRATION_TARGETS = (
    "test_infrastructure",
    "performance_platform",
    "enterprise_hub",
    "ai_provider_hub",
    "enterprise_ai_orchestrator",
    "workflow_intelligence",
    "event_platform",
    "observability",
)

KPI_TARGETS = {
    "all_load_test_kinds": True,
    "auto_bottleneck_detection": True,
    "per_service_metrics": True,
    "performance_reports": True,
    "optimization_recommendations": True,
    "required_before_production": True,
    "no_duplicated_epf_core": True,
}

PRINCIPLES = (
    "simulate_never_break_prod",
    "ci_cd_gate",
    "measure_every_layer",
    "auto_bottleneck_and_advice",
    "additive_to_epf",
    "no_duplicated_business_logic",
)
