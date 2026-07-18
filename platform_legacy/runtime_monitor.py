# Runtime monitoring — legacy vs platform calls, fallbacks, errors, latency.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from platform_legacy.coverage import migration_coverage
from platform_legacy.registry import legacy_registry


@dataclass(slots=True)
class RuntimeMonitor:
    platform_calls: int = 0
    legacy_calls: int = 0
    fallbacks: int = 0
    errors: int = 0
    total_latency_ms: float = 0.0
    call_count_for_latency: int = 0

    def record_platform(self, subsystem: str, *, method: str = "", latency_ms: float = 0.0) -> None:
        self.platform_calls += 1
        migration_coverage.record_platform(subsystem, method=method)
        self._record_latency(latency_ms)

    def record_legacy(self, subsystem: str, *, method: str = "", latency_ms: float = 0.0) -> None:
        self.legacy_calls += 1
        migration_coverage.record_legacy(subsystem, method=method)
        self._record_latency(latency_ms)

    def record_fallback(self, subsystem: str, *, reason: str = "") -> None:
        self.fallbacks += 1
        migration_coverage.record_fallback(subsystem, reason=reason)

    def record_error(self, subsystem: str, *, method: str = "") -> None:
        self.errors += 1
        migration_coverage.record_error(subsystem, method=method)

    def _record_latency(self, latency_ms: float) -> None:
        if latency_ms > 0:
            self.total_latency_ms += latency_ms
            self.call_count_for_latency += 1

    @property
    def migration_ratio(self) -> dict[str, float]:
        total = self.platform_calls + self.legacy_calls
        if total == 0:
            return {"platform_percent": 0.0, "legacy_percent": 0.0, "total_calls": 0}
        platform_pct = round(self.platform_calls / total * 100, 1)
        return {
            "platform_percent": platform_pct,
            "legacy_percent": round(100 - platform_pct, 1),
            "total_calls": total,
        }

    @property
    def avg_latency_ms(self) -> float:
        if self.call_count_for_latency == 0:
            return 0.0
        return round(self.total_latency_ms / self.call_count_for_latency, 2)

    def snapshot(self) -> dict[str, Any]:
        adapter_metrics = legacy_registry.metrics.to_dict()
        ratio = self.migration_ratio
        return {
            "platform_calls": self.platform_calls,
            "legacy_calls": self.legacy_calls,
            "fallbacks": self.fallbacks,
            "errors": self.errors + adapter_metrics.get("total_errors", 0),
            "avg_latency_ms": self.avg_latency_ms,
            "migration_ratio": ratio,
            "adapter_legacy_calls": adapter_metrics.get("total_calls", 0),
            "adapter_errors_by_name": adapter_metrics.get("errors_by_adapter", {}),
            "coverage": migration_coverage.to_dict(),
        }

    def reset(self) -> None:
        self.platform_calls = 0
        self.legacy_calls = 0
        self.fallbacks = 0
        self.errors = 0
        self.total_latency_ms = 0.0
        self.call_count_for_latency = 0
        migration_coverage.reset()


runtime_monitor = RuntimeMonitor()
