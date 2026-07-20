# Reasoning lifecycle events.

from __future__ import annotations

from dataclasses import dataclass

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class ReasoningStartedEvent(BaseEvent):
    session_id: str
    strategy: str
    agent_id: str | None = None
    request_preview: str = ""


@dataclass(kw_only=True)
class ReasoningCompletedEvent(BaseEvent):
    session_id: str
    strategy: str
    intent: str
    overall_confidence: float = 0.0
    execution_time_ms: float = 0.0
    reasoning_depth: int = 0


@dataclass(kw_only=True)
class ReasoningFailedEvent(BaseEvent):
    session_id: str
    strategy: str
    error: str
    agent_id: str | None = None
