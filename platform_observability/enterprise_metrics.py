# Enterprise platform metrics catalog — Sprint 32.3.
# Extends platform_observability; does not replace MetricsService.

from __future__ import annotations

from typing import Any

from platform_observability.metrics_service import METRIC_CATALOG, MetricsService

ENTERPRISE_METRIC_CATALOG: dict[str, str] = {
    **METRIC_CATALOG,
    "queue.wait_ms": "Time spent waiting in unified queue before execution",
    "queue.depth": "Unified queue depth by lane",
    "api.latency_ms": "API end-to-end latency",
    "ai.cost_usd": "AI provider spend (USD)",
    "ai.tokens": "AI tokens consumed",
    "runtime.health": "Enterprise Runtime aggregate health (0=err,1=warn,2=ok)",
    "provider.requests": "AI / integration provider request count",
    "cache.hit_rate": "Cache hit rate (0–1)",
    "workflow.duration_ms": "Workflow execution duration",
    "notification.delivery_ms": "Notification pipeline delivery latency",
    "render.queue_ms": "Render lane queue wait",
}


class EnterpriseMetrics:
    """Thin facade over MetricsService with Sprint 32.3 enterprise names."""

    def __init__(self, service: MetricsService | None = None) -> None:
        self._service = service or MetricsService()

    def catalog(self) -> dict[str, str]:
        return dict(ENTERPRISE_METRIC_CATALOG)

    def record_queue_wait(self, ms: float, *, lane: str) -> None:
        self._service.record("queue.wait_ms", ms, unit="ms", tags={"lane": lane})

    def record_api_latency(self, ms: float, *, route: str = "") -> None:
        self._service.record("api.latency_ms", ms, unit="ms", tags={"route": route})

    def record_ai_cost(self, usd: float, *, provider: str = "") -> None:
        self._service.record("ai.cost_usd", usd, unit="usd", tags={"provider": provider})

    def record_runtime_health(self, level: float) -> None:
        self._service.record("runtime.health", level, unit="level")

    def record_provider_usage(self, count: float = 1.0, *, provider: str) -> None:
        self._service.record("provider.requests", count, unit="count", tags={"provider": provider})

    def record_cache_hit_rate(self, rate: float) -> None:
        self._service.record("cache.hit_rate", max(0.0, min(1.0, rate)), unit="ratio")

    def record_workflow_duration(self, ms: float, *, workflow_id: str = "") -> None:
        self._service.record(
            "workflow.duration_ms", ms, unit="ms", tags={"workflow_id": workflow_id}
        )

    def snapshot_names(self) -> list[str]:
        return sorted(ENTERPRISE_METRIC_CATALOG.keys())

    def capabilities(self) -> dict[str, Any]:
        return {
            "metrics": self.snapshot_names(),
            "system_of_record": "platform_observability.MetricsService",
            "sprint": "32.3",
        }


enterprise_metrics = EnterpriseMetrics()
