# Decision engine metrics.

from __future__ import annotations

import time
from dataclasses import dataclass, field

from platform_decision.models import DecisionResult


@dataclass
class DecisionMetricEntry:
    decision_id: str
    strategy: str
    policy_id: str
    confidence: float
    success: bool
    decision_time_ms: float
    alternatives_evaluated: int
    timestamp: float = field(default_factory=time.time)


class DecisionMetrics:
    def __init__(self) -> None:
        self._entries: list[DecisionMetricEntry] = []
        self._policy_usage: dict[str, int] = {}

    def reset(self) -> None:
        self._entries.clear()
        self._policy_usage.clear()

    def record(self, result: DecisionResult) -> None:
        alt_count = len(result.alternatives)
        self._entries.append(
            DecisionMetricEntry(
                decision_id=result.decision_id,
                strategy=result.strategy.value,
                policy_id=result.policy_id,
                confidence=result.confidence,
                success=result.success,
                decision_time_ms=result.decision_time_ms,
                alternatives_evaluated=alt_count + 1,
            )
        )
        self._policy_usage[result.policy_id] = self._policy_usage.get(result.policy_id, 0) + 1

    def summary(self) -> dict:
        total = len(self._entries)
        if total == 0:
            return {
                "decisions": 0,
                "avg_decision_latency_ms": 0.0,
                "avg_confidence": 0.0,
                "success_rate": 0.0,
                "avg_alternatives_evaluated": 0.0,
                "policy_usage": {},
            }
        successes = sum(1 for e in self._entries if e.success)
        return {
            "decisions": total,
            "avg_decision_latency_ms": round(sum(e.decision_time_ms for e in self._entries) / total, 2),
            "avg_confidence": round(sum(e.confidence for e in self._entries) / total, 2),
            "success_rate": round(successes / total, 4),
            "avg_alternatives_evaluated": round(sum(e.alternatives_evaluated for e in self._entries) / total, 1),
            "policy_usage": dict(self._policy_usage),
        }


decision_metrics = DecisionMetrics()
