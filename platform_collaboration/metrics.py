# Collaboration engine metrics.

from __future__ import annotations

import time
from dataclasses import dataclass, field

from platform_collaboration.models import CollaborationResult


@dataclass
class CollaborationMetricEntry:
    session_id: str
    mode: str
    success: bool
    collaboration_time_ms: float
    consensus_time_ms: float
    delegations: int
    conflicts: int
    participant_count: int
    timestamp: float = field(default_factory=time.time)


class CollaborationMetrics:
    def __init__(self) -> None:
        self._entries: list[CollaborationMetricEntry] = []
        self._agent_participation: dict[str, int] = {}

    def reset(self) -> None:
        self._entries.clear()
        self._agent_participation.clear()

    def record(self, result: CollaborationResult) -> None:
        consensus_ms = sum(c.consensus_time_ms for c in result.consensus_results)
        self._entries.append(
            CollaborationMetricEntry(
                session_id=result.session.session_id,
                mode=result.session.mode.value,
                success=result.success,
                collaboration_time_ms=result.session.collaboration_time_ms,
                consensus_time_ms=consensus_ms,
                delegations=result.delegations,
                conflicts=result.conflicts_detected,
                participant_count=len(result.session.participants),
            )
        )
        for aid in result.session.participants:
            self._agent_participation[aid] = self._agent_participation.get(aid, 0) + 1

    def summary(self) -> dict:
        total = len(self._entries)
        if total == 0:
            return {
                "collaborations": 0,
                "avg_collaboration_latency_ms": 0.0,
                "avg_consensus_time_ms": 0.0,
                "total_delegations": 0,
                "total_conflicts": 0,
                "agent_participation": {},
                "success_rate": 0.0,
            }
        successes = sum(1 for e in self._entries if e.success)
        return {
            "collaborations": total,
            "avg_collaboration_latency_ms": round(sum(e.collaboration_time_ms for e in self._entries) / total, 2),
            "avg_consensus_time_ms": round(sum(e.consensus_time_ms for e in self._entries) / total, 2),
            "total_delegations": sum(e.delegations for e in self._entries),
            "total_conflicts": sum(e.conflicts for e in self._entries),
            "agent_participation": dict(self._agent_participation),
            "success_rate": round(successes / total, 4),
        }


collaboration_metrics = CollaborationMetrics()
