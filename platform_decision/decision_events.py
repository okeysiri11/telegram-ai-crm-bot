# Decision lifecycle events.

from __future__ import annotations

from dataclasses import dataclass

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class DecisionStartedEvent(BaseEvent):
    decision_id: str
    candidate_count: int
    strategy: str
    policy_id: str
    agent_id: str | None = None


@dataclass(kw_only=True)
class DecisionCompletedEvent(BaseEvent):
    decision_id: str
    selected_candidate_id: str
    confidence: float
    strategy: str
    policy_id: str
    decision_time_ms: float = 0.0
    alternatives_count: int = 0


@dataclass(kw_only=True)
class DecisionFailedEvent(BaseEvent):
    decision_id: str
    error: str
    strategy: str = ""
