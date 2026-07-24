"""AI Usage Analytics — Sprint 24.9."""

from __future__ import annotations

from typing import Any


class AIUsageAnalytics:
    def summarize(self, *, requests: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        requests = list(requests or [])
        total = len(requests)
        success = sum(1 for r in requests if r.get("success"))
        fallbacks = sum(1 for r in requests if r.get("fallback_used"))
        latencies = [float(r.get("latency_ms", 0)) for r in requests]
        costs = [float(r.get("cost", 0)) for r in requests]
        qualities = [float(r.get("quality", 0)) for r in requests if r.get("quality") is not None]
        models: dict[str, int] = {}
        for r in requests:
            mid = r.get("model_id", "unknown")
            models[mid] = models.get(mid, 0) + 1
        return {
            "request_count": total,
            "success_rate": round(success / total, 3) if total else 0.0,
            "avg_latency_ms": round(sum(latencies) / total, 2) if total else 0.0,
            "total_cost": round(sum(costs), 6),
            "avg_quality": round(sum(qualities) / len(qualities), 3) if qualities else None,
            "fallback_pct": round(fallbacks / total, 3) if total else 0.0,
            "model_popularity": models,
        }
