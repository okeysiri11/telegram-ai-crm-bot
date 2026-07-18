# Performance monitor — API latency and slow request tracking.

from __future__ import annotations

import time
from collections import defaultdict
from typing import Any

from platform_observability.metrics_service import metrics_service


class PerformanceMonitor:
    def __init__(self, *, slow_threshold_ms: float = 1000) -> None:
        self._latencies: dict[str, list[float]] = defaultdict(list)
        self._slow_requests: list[dict[str, Any]] = []
        self._slow_threshold_ms = slow_threshold_ms

    def reset(self) -> None:
        self._latencies.clear()
        self._slow_requests.clear()

    def record_request(
        self,
        *,
        path: str,
        method: str,
        duration_ms: float,
        status: int = 200,
    ) -> None:
        key = f"{method} {path}"
        self._latencies[key].append(duration_ms)
        metrics_service.record(
            "api.request.duration_ms",
            duration_ms,
            unit="ms",
            tags={"path": path, "method": method, "status": str(status)},
        )

        if duration_ms >= self._slow_threshold_ms:
            self._slow_requests.append(
                {
                    "path": path,
                    "method": method,
                    "duration_ms": duration_ms,
                    "status": status,
                    "recorded_at": time.time(),
                }
            )
            if len(self._slow_requests) > 1000:
                self._slow_requests = self._slow_requests[-1000:]

    def slowest_apis(self, *, limit: int = 10) -> list[dict[str, Any]]:
        ranked: list[tuple[str, float]] = []
        for key, values in self._latencies.items():
            if values:
                ranked.append((key, sum(values) / len(values)))
        ranked.sort(key=lambda x: x[1], reverse=True)
        return [{"endpoint": k, "avg_duration_ms": round(v, 2)} for k, v in ranked[:limit]]

    def slow_requests(self, *, limit: int = 20) -> list[dict[str, Any]]:
        return self._slow_requests[-limit:]

    def summary(self) -> dict[str, Any]:
        total = sum(len(v) for v in self._latencies.values())
        if total == 0:
            return {"requests_tracked": 0}
        all_values = [v for vals in self._latencies.values() for v in vals]
        return {
            "requests_tracked": total,
            "avg_duration_ms": round(sum(all_values) / len(all_values), 2),
            "p95_duration_ms": round(sorted(all_values)[int(len(all_values) * 0.95) - 1], 2)
            if len(all_values) >= 20
            else round(max(all_values), 2),
            "slow_request_count": len(self._slow_requests),
        }


performance_monitor = PerformanceMonitor()
