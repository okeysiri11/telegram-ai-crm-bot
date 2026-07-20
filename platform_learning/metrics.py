# Learning engine metrics.

from __future__ import annotations

import time
from dataclasses import dataclass, field

from platform_learning.models import LearningResult


@dataclass
class LearningMetricEntry:
    session_id: str
    agent_id: str | None
    feedback_volume: int
    patterns_detected: int
    recommendations_count: int
    cycle_time_ms: float
    success: bool
    timestamp: float = field(default_factory=time.time)


class LearningMetrics:
    def __init__(self) -> None:
        self._entries: list[LearningMetricEntry] = []
        self._agent_scores: dict[str, float] = {}
        self._workflow_scores: dict[str, float] = {}

    def reset(self) -> None:
        self._entries.clear()
        self._agent_scores.clear()
        self._workflow_scores.clear()

    def record(self, result: LearningResult) -> None:
        patterns = len(result.success_patterns) + len(result.failure_patterns)
        self._entries.append(
            LearningMetricEntry(
                session_id=result.session.session_id,
                agent_id=result.session.agent_id,
                feedback_volume=result.insights.get("feedback_volume", 0),
                patterns_detected=patterns,
                recommendations_count=len(result.recommendations),
                cycle_time_ms=result.session.cycle_time_ms,
                success=result.success,
            )
        )
        agent_id = result.session.agent_id
        if agent_id:
            success_ratio = result.insights.get("success_patterns", 0) / max(patterns, 1)
            prev = self._agent_scores.get(agent_id, 50.0)
            self._agent_scores[agent_id] = round(prev * 0.7 + success_ratio * 100 * 0.3, 2)

        wf_success = result.insights.get("success_patterns", 0)
        wf_fail = result.insights.get("failure_patterns", 0)
        if wf_success + wf_fail > 0:
            score = round(wf_success / (wf_success + wf_fail) * 100, 2)
            self._workflow_scores["global"] = score

    def summary(self) -> dict:
        total = len(self._entries)
        if total == 0:
            return {
                "learning_cycles": 0,
                "recommendation_acceptance_rate": 0.0,
                "pattern_detection_rate": 0.0,
                "agent_improvement_score": 0.0,
                "workflow_improvement_score": 0.0,
                "feedback_volume": 0,
            }
        return {
            "learning_cycles": total,
            "recommendation_acceptance_rate": 0.0,  # updated via engine.accept_recommendation
            "pattern_detection_rate": round(sum(e.patterns_detected for e in self._entries) / total, 2),
            "agent_improvement_score": round(sum(self._agent_scores.values()) / max(len(self._agent_scores), 1), 2),
            "workflow_improvement_score": self._workflow_scores.get("global", 0.0),
            "feedback_volume": sum(e.feedback_volume for e in self._entries),
        }


learning_metrics = LearningMetrics()
