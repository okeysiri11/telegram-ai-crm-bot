# Decision domain models.

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DecisionStrategyType(str, Enum):
    RULE_BASED = "rule_based"
    WEIGHTED_SCORING = "weighted_scoring"
    COST_OPTIMIZATION = "cost_optimization"
    RISK_AWARE = "risk_aware"
    TIME_OPTIMIZATION = "time_optimization"
    CONFIDENCE_AWARE = "confidence_aware"
    MULTI_CRITERIA = "multi_criteria"
    FALLBACK = "fallback"


@dataclass
class DecisionCriteria:
    """Scoring dimensions for candidate evaluation."""

    execution_cost: float = 0.0
    estimated_duration_ms: float = 0.0
    risk_level: float = 0.0  # 0=low, 100=high
    confidence_score: float = 0.0
    tool_availability: float = 0.0
    agent_availability: float = 0.0
    resource_consumption: float = 0.0
    business_priority: float = 0.0
    user_preference: float = 0.0

    def to_dict(self) -> dict[str, float]:
        return {
            "execution_cost": self.execution_cost,
            "estimated_duration_ms": self.estimated_duration_ms,
            "risk_level": self.risk_level,
            "confidence_score": self.confidence_score,
            "tool_availability": self.tool_availability,
            "agent_availability": self.agent_availability,
            "resource_consumption": self.resource_consumption,
            "business_priority": self.business_priority,
            "user_preference": self.user_preference,
        }


@dataclass
class DecisionScore:
    candidate_id: str
    total_score: float = 0.0
    dimension_scores: dict[str, float] = field(default_factory=dict)
    rank: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "total_score": self.total_score,
            "dimension_scores": dict(self.dimension_scores),
            "rank": self.rank,
        }


@dataclass
class DecisionCandidate:
    """An execution alternative to evaluate."""

    candidate_id: str
    name: str
    description: str = ""
    capability: str | None = None
    agent_id: str | None = None
    plan_id: str | None = None
    criteria: DecisionCriteria = field(default_factory=DecisionCriteria)
    metadata: dict[str, Any] = field(default_factory=dict)
    valid: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "name": self.name,
            "description": self.description,
            "capability": self.capability,
            "agent_id": self.agent_id,
            "criteria": self.criteria.to_dict(),
            "valid": self.valid,
        }


@dataclass
class DecisionContext:
    """Input context for decision-making."""

    request: str
    agent_id: str | None = None
    user_id: str | None = None
    candidates: list[DecisionCandidate] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    reasoning_result: dict[str, Any] = field(default_factory=dict)
    planning_result: dict[str, Any] = field(default_factory=dict)
    memory_context: dict[str, Any] = field(default_factory=dict)
    user_preferences: dict[str, Any] = field(default_factory=dict)
    business_priority: float = 50.0
    available_tools: list[str] = field(default_factory=list)
    available_agents: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DecisionTrace:
    decision_id: str
    strategy: str
    policy_id: str
    steps: list[dict[str, Any]] = field(default_factory=list)
    alternatives: list[dict[str, Any]] = field(default_factory=list)
    debug: dict[str, Any] = field(default_factory=dict)

    def add_step(self, phase: str, description: str, **extra: Any) -> None:
        self.steps.append({"phase": phase, "description": description, **extra})

    def human_readable(self) -> str:
        lines = [f"Decision trace ({self.strategy}, policy={self.policy_id}):"]
        for i, step in enumerate(self.steps, 1):
            lines.append(f"  {i}. [{step['phase']}] {step['description']}")
        if self.alternatives:
            lines.append("  Alternatives retained:")
            for alt in self.alternatives[:5]:
                lines.append(f"    - {alt.get('name', alt.get('candidate_id'))}: score={alt.get('total_score', 0):.1f}")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "strategy": self.strategy,
            "policy_id": self.policy_id,
            "steps": list(self.steps),
            "alternatives": list(self.alternatives),
        }


@dataclass
class DecisionResult:
    decision_id: str
    selected: DecisionCandidate
    ranked: list[DecisionScore] = field(default_factory=list)
    alternatives: list[DecisionCandidate] = field(default_factory=list)
    confidence: float = 0.0
    trace: DecisionTrace | None = None
    strategy: DecisionStrategyType = DecisionStrategyType.MULTI_CRITERIA
    policy_id: str = "balanced"
    success: bool = True
    error: str | None = None
    decision_time_ms: float = 0.0

    def explanation(self) -> str:
        lines = [
            f"Selected: {self.selected.name} ({self.selected.candidate_id})",
            f"Strategy: {self.strategy.value}",
            f"Policy: {self.policy_id}",
            f"Confidence: {self.confidence:.1f}%",
            f"Score: {self.ranked[0].total_score:.2f}" if self.ranked else "",
        ]
        if self.trace:
            lines.append("")
            lines.append(self.trace.human_readable())
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "selected": self.selected.to_dict(),
            "ranked": [s.to_dict() for s in self.ranked],
            "alternatives_count": len(self.alternatives),
            "confidence": self.confidence,
            "trace": self.trace.to_dict() if self.trace else {},
            "strategy": self.strategy.value,
            "policy_id": self.policy_id,
            "success": self.success,
            "decision_time_ms": self.decision_time_ms,
        }
