# Planning lifecycle events.

from __future__ import annotations

from dataclasses import dataclass

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class PlanningStartedEvent(BaseEvent):
    plan_id: str
    goal: str
    strategy: str
    agent_id: str | None = None


@dataclass(kw_only=True)
class PlanningCompletedEvent(BaseEvent):
    plan_id: str
    step_count: int
    estimated_cost: float
    planning_time_ms: float = 0.0


@dataclass(kw_only=True)
class PlanningFailedEvent(BaseEvent):
    plan_id: str
    error: str


@dataclass(kw_only=True)
class ReplanningTriggeredEvent(BaseEvent):
    plan_id: str
    failed_step_id: str
    replan_count: int = 0
