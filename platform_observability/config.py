# Observability layer configuration.

from __future__ import annotations

from dataclasses import dataclass, field

from platform_observability.models import AlertThreshold, AlertSeverity


@dataclass(frozen=True)
class ObservabilityConfig:
    slow_workflow_ms: float = 5000.0
    high_error_rate: float = 0.1
    memory_pressure_percent: float = 90.0
    queue_overflow_size: float = 1000.0
    metrics_collection_interval_sec: float = 60.0
    trace_export_batch_size: int = 100


DEFAULT_OBSERVABILITY_CONFIG = ObservabilityConfig()

DEFAULT_ALERT_THRESHOLDS: list[AlertThreshold] = [
    AlertThreshold("high_error_rate", "platform.error_rate", "gt", 0.1, AlertSeverity.CRITICAL.value),
    AlertThreshold("slow_workflows", "workflow.duration_ms", "gt", 5000.0, AlertSeverity.WARNING.value),
    AlertThreshold("agent_failures", "agent.failure_rate", "gt", 0.2, AlertSeverity.WARNING.value),
    AlertThreshold("tool_failures", "tool.failure_rate", "gt", 0.2, AlertSeverity.WARNING.value),
    AlertThreshold("memory_pressure", "system.memory.percent", "gt", 90.0, AlertSeverity.CRITICAL.value),
    AlertThreshold("queue_overflow", "jobs.queue.size", "gt", 1000.0, AlertSeverity.CRITICAL.value),
]
