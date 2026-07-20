# Reliability metrics.

from __future__ import annotations

import time
from dataclasses import dataclass, field

from platform_reliability.models import RecoveryResult


@dataclass
class ReliabilityMetricEntry:
    success: bool
    action: str
    recovery_time_ms: float
    attempts: int
    timestamp: float = field(default_factory=time.time)


class ReliabilityMetrics:
    def __init__(self) -> None:
        self._recoveries: list[ReliabilityMetricEntry] = []
        self._failures: list[float] = []

    def reset(self) -> None:
        self._recoveries.clear()
        self._failures.clear()

    def record_recovery(self, result: RecoveryResult) -> None:
        self._recoveries.append(
            ReliabilityMetricEntry(
                success=result.success,
                action=result.action.value,
                recovery_time_ms=result.recovery_time_ms,
                attempts=result.attempts,
            )
        )

    def record_failure(self) -> None:
        self._failures.append(time.time())

    def summary(self) -> dict:
        total = len(self._recoveries)
        if total == 0:
            return {
                "recovery_success_rate": 0.0,
                "retry_count": 0,
                "circuit_breaker_events": 0,
                "avg_recovery_latency_ms": 0.0,
                "availability": 1.0,
                "mttr_ms": 0.0,
                "failure_frequency": len(self._failures),
            }

        from platform_reliability.circuit_breaker import circuit_breaker
        from platform_reliability.retry_manager import retry_manager

        successes = sum(1 for r in self._recoveries if r.success)
        retry_metrics = retry_manager.metrics()
        recovery_times = [r.recovery_time_ms for r in self._recoveries if r.recovery_time_ms > 0]

        return {
            "recovery_success_rate": round(successes / total, 4),
            "retry_count": retry_metrics.get("retries", 0),
            "circuit_breaker_events": len(circuit_breaker.event_log()),
            "avg_recovery_latency_ms": round(sum(recovery_times) / max(len(recovery_times), 1), 2),
            "availability": round(successes / max(total + len(self._failures), 1), 4),
            "mttr_ms": round(sum(recovery_times) / max(successes, 1), 2),
            "failure_frequency": len(self._failures),
        }


reliability_metrics = ReliabilityMetrics()
