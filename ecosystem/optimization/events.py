# Optimization events — Sprint 7.5.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class OptimizationStartedEvent(BaseEvent):
    run_id: str = ""
    scope: str = ""


@dataclass(kw_only=True)
class RecommendationGeneratedEvent(BaseEvent):
    recommendation_id: str = ""
    category: str = ""
    title: str = ""
    priority: int = 0


@dataclass(kw_only=True)
class SimulationCompletedEvent(BaseEvent):
    simulation_id: str = ""
    simulation_type: str = ""
    risk_score: float = 0.0


@dataclass(kw_only=True)
class LearningCycleCompletedEvent(BaseEvent):
    cycle_id: str = ""
    records_analyzed: int = 0
    insights: list[str] = field(default_factory=list)


@dataclass(kw_only=True)
class PerformanceUpdatedEvent(BaseEvent):
    snapshot_id: str = ""
    domain: str = ""
    name: str = ""
    value: float = 0.0


@dataclass(kw_only=True)
class StrategyUpdatedEvent(BaseEvent):
    strategy_id: str = ""
    title: str = ""
    focus: str = ""
