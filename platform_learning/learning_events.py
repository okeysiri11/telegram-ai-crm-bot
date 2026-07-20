# Learning lifecycle events.

from __future__ import annotations

from dataclasses import dataclass

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class LearningCycleStartedEvent(BaseEvent):
    session_id: str
    agent_id: str | None = None


@dataclass(kw_only=True)
class LearningCycleCompletedEvent(BaseEvent):
    session_id: str
    recommendations_count: int
    patterns_detected: int
    cycle_time_ms: float = 0.0


@dataclass(kw_only=True)
class FeedbackReceivedEvent(BaseEvent):
    feedback_id: str
    source: str
    sentiment: str
    agent_id: str | None = None


@dataclass(kw_only=True)
class RecommendationGeneratedEvent(BaseEvent):
    session_id: str
    recommendation_id: str
    recommendation_type: str


@dataclass(kw_only=True)
class LearningFailedEvent(BaseEvent):
    session_id: str
    error: str
