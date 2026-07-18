# Skill execution metrics.

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from platform_ai.skills.models import SkillExecutionResult


@dataclass
class SkillMetricEntry:
    skill_id: str
    success: bool
    latency_ms: float
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    timestamp: float = field(default_factory=time.time)


class SkillMetrics:
    def __init__(self) -> None:
        self._entries: list[SkillMetricEntry] = []

    def reset(self) -> None:
        self._entries.clear()

    def record(self, result: SkillExecutionResult) -> None:
        self._entries.append(
            SkillMetricEntry(
                skill_id=result.skill_id,
                success=result.success,
                latency_ms=result.latency_ms,
                tokens_in=result.tokens_in,
                tokens_out=result.tokens_out,
                cost_usd=result.cost_usd,
            )
        )

    def for_skill(self, skill_id: str) -> dict[str, Any]:
        entries = [e for e in self._entries if e.skill_id == skill_id]
        if not entries:
            return {
                "skill_id": skill_id,
                "executions": 0,
                "success_rate": 0.0,
                "failures": 0,
                "avg_latency_ms": 0.0,
                "avg_tokens": 0.0,
                "avg_cost_usd": 0.0,
            }
        successes = sum(1 for e in entries if e.success)
        failures = len(entries) - successes
        avg_latency = sum(e.latency_ms for e in entries) / len(entries)
        avg_tokens = sum(e.tokens_in + e.tokens_out for e in entries) / len(entries)
        avg_cost = sum(e.cost_usd for e in entries) / len(entries)
        return {
            "skill_id": skill_id,
            "executions": len(entries),
            "success_rate": round(successes / len(entries), 4),
            "failures": failures,
            "avg_latency_ms": round(avg_latency, 2),
            "avg_tokens": round(avg_tokens, 1),
            "avg_cost_usd": round(avg_cost, 6),
        }

    def summary(self) -> dict[str, Any]:
        skill_ids = {e.skill_id for e in self._entries}
        return {
            "total_executions": len(self._entries),
            "skills": {sid: self.for_skill(sid) for sid in sorted(skill_ids)},
        }


skill_metrics = SkillMetrics()
