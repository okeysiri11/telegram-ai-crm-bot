"""Metrics Collector — Sprint 25.6."""

from __future__ import annotations

from typing import Any

from platform_enterprise_production.models import METRIC_KINDS


class MetricsCollector:
    def collect(self, *, overrides: dict[str, float] | None = None) -> dict[str, Any]:
        overrides = overrides or {}
        defaults = {
            "requests_per_sec": 120.0,
            "response_time": 85.0,
            "error_rate": 0.002,
            "queue_size": 12.0,
            "active_users": 340.0,
            "active_companies": 28.0,
            "ai_requests": 55.0,
            "workflow_executions": 40.0,
            "database_connections": 64.0,
        }
        metrics = [{
            "kind": k,
            "value": float(overrides.get(k, defaults[k])),
        } for k in METRIC_KINDS]
        return {"metrics": metrics, "count": len(metrics), "collected": True}
