# Optimization models — Sprint 7.5.

from __future__ import annotations

import enum
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


def _id() -> str:
    return str(uuid.uuid4())


def _ts() -> float:
    return time.time()


class RecommendationCategory(str, enum.Enum):
    OPTIMIZATION = "optimization"
    ARCHITECTURE = "architecture"
    WORKFLOW = "workflow"
    COST = "cost"
    RESOURCE = "resource"
    SCALING = "scaling"


class SimulationType(str, enum.Enum):
    WHAT_IF = "what_if"
    BUSINESS = "business"
    AGENT_STRATEGY = "agent_strategy"
    WORKFLOW = "workflow"
    RISK = "risk"
    CAPACITY = "capacity"


class MetricDomain(str, enum.Enum):
    APPLICATION = "application"
    AGENT = "agent"
    WORKFLOW = "workflow"
    LATENCY = "latency"
    RESOURCE = "resource"
    BUSINESS = "business"


@dataclass
class ExecutionRecord:
    record_id: str = field(default_factory=_id)
    source: str = ""
    action: str = ""
    outcome: str = "success"
    duration_ms: float = 0.0
    application_id: str = ""
    agent_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "source": self.source,
            "action": self.action,
            "outcome": self.outcome,
            "duration_ms": self.duration_ms,
            "application_id": self.application_id,
            "agent_id": self.agent_id,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }


@dataclass
class DecisionOutcome:
    outcome_id: str = field(default_factory=_id)
    decision_id: str = ""
    decision_type: str = ""
    expected: str = ""
    actual: str = ""
    success: bool = True
    score: float = 1.0
    lessons: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome_id": self.outcome_id,
            "decision_id": self.decision_id,
            "decision_type": self.decision_type,
            "expected": self.expected,
            "actual": self.actual,
            "success": self.success,
            "score": self.score,
            "lessons": list(self.lessons),
            "created_at": self.created_at,
        }


@dataclass
class FeedbackItem:
    feedback_id: str = field(default_factory=_id)
    source: str = "user"
    target_type: str = "workflow"
    target_id: str = ""
    rating: float = 0.0
    comment: str = ""
    tags: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "feedback_id": self.feedback_id,
            "source": self.source,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "rating": self.rating,
            "comment": self.comment,
            "tags": list(self.tags),
            "created_at": self.created_at,
        }


@dataclass
class LearningCycle:
    cycle_id: str = field(default_factory=_id)
    status: str = "completed"
    records_analyzed: int = 0
    insights: list[str] = field(default_factory=list)
    refinements: list[dict[str, Any]] = field(default_factory=list)
    replayed: int = 0
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "status": self.status,
            "records_analyzed": self.records_analyzed,
            "insights": list(self.insights),
            "refinements": list(self.refinements),
            "replayed": self.replayed,
            "created_at": self.created_at,
        }


@dataclass
class PerformanceSnapshot:
    snapshot_id: str = field(default_factory=_id)
    domain: MetricDomain = MetricDomain.APPLICATION
    name: str = ""
    value: float = 0.0
    unit: str = ""
    target: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "domain": self.domain.value,
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "target": self.target,
            "on_target": self.value <= self.target if self.unit in ("ms", "percent_util") else self.value >= self.target,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }


@dataclass
class BenchmarkResult:
    benchmark_id: str = field(default_factory=_id)
    name: str = ""
    score: float = 0.0
    baseline: float = 0.0
    delta: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "benchmark_id": self.benchmark_id,
            "name": self.name,
            "score": self.score,
            "baseline": self.baseline,
            "delta": self.delta,
            "details": dict(self.details),
            "created_at": self.created_at,
        }


@dataclass
class Recommendation:
    recommendation_id: str = field(default_factory=_id)
    category: RecommendationCategory = RecommendationCategory.OPTIMIZATION
    title: str = ""
    description: str = ""
    priority: int = 50
    impact: str = "medium"
    estimated_gain: float = 0.0
    actions: list[str] = field(default_factory=list)
    status: str = "open"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "category": self.category.value,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "impact": self.impact,
            "estimated_gain": self.estimated_gain,
            "actions": list(self.actions),
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass
class SimulationRun:
    simulation_id: str = field(default_factory=_id)
    simulation_type: SimulationType = SimulationType.WHAT_IF
    name: str = ""
    assumptions: dict[str, Any] = field(default_factory=dict)
    results: dict[str, Any] = field(default_factory=dict)
    risk_score: float = 0.0
    status: str = "completed"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "simulation_id": self.simulation_id,
            "simulation_type": self.simulation_type.value,
            "name": self.name,
            "assumptions": dict(self.assumptions),
            "results": dict(self.results),
            "risk_score": self.risk_score,
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass
class StrategyUpdate:
    strategy_id: str = field(default_factory=_id)
    title: str = ""
    focus: str = ""
    objectives: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    status: str = "active"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "title": self.title,
            "focus": self.focus,
            "objectives": list(self.objectives),
            "recommendations": list(self.recommendations),
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass
class OptimizationRun:
    run_id: str = field(default_factory=_id)
    status: str = "completed"
    learning_cycle_id: str = ""
    recommendation_ids: list[str] = field(default_factory=list)
    simulation_ids: list[str] = field(default_factory=list)
    summary: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "status": self.status,
            "learning_cycle_id": self.learning_cycle_id,
            "recommendation_ids": list(self.recommendation_ids),
            "simulation_ids": list(self.simulation_ids),
            "summary": self.summary,
            "created_at": self.created_at,
        }
