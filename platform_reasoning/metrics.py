# Reasoning engine metrics.

from __future__ import annotations

import time
from dataclasses import dataclass, field

from platform_reasoning.models import ReasoningResult


@dataclass
class ReasoningMetricEntry:
    session_id: str
    strategy: str
    success: bool
    overall_confidence: float
    execution_time_ms: float
    depth: int
    timestamp: float = field(default_factory=time.time)


class ReasoningMetrics:
    def __init__(self) -> None:
        self._entries: list[ReasoningMetricEntry] = []

    def reset(self) -> None:
        self._entries.clear()

    def record(self, result: ReasoningResult) -> None:
        self._entries.append(
            ReasoningMetricEntry(
                session_id=result.session_id,
                strategy=result.strategy.value,
                success=result.success,
                overall_confidence=result.confidence.overall,
                execution_time_ms=result.execution_time_ms,
                depth=result.trace.depth,
            )
        )

    def summary(self) -> dict:
        total = len(self._entries)
        if total == 0:
            return {
                "sessions": 0,
                "avg_reasoning_time_ms": 0.0,
                "avg_confidence": 0.0,
                "strategy_usage": {},
                "avg_depth": 0.0,
                "confidence_distribution": {"high": 0, "medium": 0, "low": 0},
            }

        confidences = [e.overall_confidence for e in self._entries]
        strategies: dict[str, int] = {}
        for e in self._entries:
            strategies[e.strategy] = strategies.get(e.strategy, 0) + 1

        high = sum(1 for c in confidences if c >= 75)
        medium = sum(1 for c in confidences if 50 <= c < 75)
        low = sum(1 for c in confidences if c < 50)

        return {
            "sessions": total,
            "avg_reasoning_time_ms": round(sum(e.execution_time_ms for e in self._entries) / total, 2),
            "avg_confidence": round(sum(confidences) / total, 2),
            "strategy_usage": strategies,
            "avg_depth": round(sum(e.depth for e in self._entries) / total, 1),
            "confidence_distribution": {"high": high, "medium": medium, "low": low},
        }


reasoning_metrics = ReasoningMetrics()
