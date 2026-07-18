# Smart assignment events — scoring pipeline lifecycle.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class SmartAssignmentCalculatedEvent(BaseEvent):
    request_id: str | None = None
    request_number: str | None = None
    segment: str
    strategy: str = "SMART"
    candidate_count: int = 0
    scores: list[dict[str, Any]] = field(default_factory=list)
    selected_pool_id: str | None = None
    selected_score: float = 0.0
    assignment_latency_ms: float = 0.0


@dataclass(kw_only=True)
class SmartAssignmentCompletedEvent(BaseEvent):
    assignment_id: str
    request_id: str | None = None
    request_number: str | None = None
    segment: str
    strategy: str
    manager_pool_id: str
    manager_id: str | None = None
    manager_telegram_id: int
    manager_name: str = ""
    score: float = 0.0
    specialization: str | None = None
