"""Performance platform constants — Sprint 21.7."""

from __future__ import annotations

PROFILE_TARGETS = (
    "api",
    "ai_orchestrator",
    "workflow",
    "event_bus",
    "data_fabric",
    "knowledge_platform",
    "enterprise_hub",
)

RESOURCE_DIMENSIONS = ("cpu", "memory", "disk", "network")

CACHE_BACKENDS = ("redis", "local", "distributed")

LOAD_TARGETS = (
    "rest_api",
    "websocket",
    "ai_requests",
    "workflow",
    "event_bus",
    "bulk_import",
    "report_generation",
)

MONITOR_METRICS = (
    "response_time",
    "throughput",
    "error_rate",
    "cpu",
    "ram",
    "io",
    "network",
    "queue_depth",
)

SLA = {
    "api_p95_ms": 100.0,
    "api_throughput_rps": 500.0,
    "event_bus_tps": 1000.0,
    "workflow_p95_ms": 250.0,
    "ai_p95_ms": 800.0,
    "error_rate_max": 0.01,
    "recovery_time_s": 30.0,
}

INTEGRATION_TARGETS = (
    "kubernetes",
    "redis",
    "observability",
    "event_platform",
    "quality_assurance",
    "enterprise_hub",
)
