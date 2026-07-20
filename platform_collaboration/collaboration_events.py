# Collaboration lifecycle events.

from __future__ import annotations

from dataclasses import dataclass

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class CollaborationStartedEvent(BaseEvent):
    session_id: str
    goal: str
    mode: str
    agent_count: int = 0


@dataclass(kw_only=True)
class AgentJoinedEvent(BaseEvent):
    session_id: str
    agent_id: str
    role: str = "worker"


@dataclass(kw_only=True)
class TaskDelegatedEvent(BaseEvent):
    session_id: str
    task_id: str
    agent_id: str
    capability: str | None = None


@dataclass(kw_only=True)
class ConsensusReachedEvent(BaseEvent):
    session_id: str
    decision: str
    confidence: float
    model: str = "majority"


@dataclass(kw_only=True)
class ConflictDetectedEvent(BaseEvent):
    session_id: str
    conflict_type: str
    description: str = ""


@dataclass(kw_only=True)
class ConflictResolvedEvent(BaseEvent):
    session_id: str
    conflict_type: str


@dataclass(kw_only=True)
class CollaborationCompletedEvent(BaseEvent):
    session_id: str
    success: bool
    completed_tasks: int = 0
    collaboration_time_ms: float = 0.0


@dataclass(kw_only=True)
class CollaborationFailedEvent(BaseEvent):
    session_id: str
    error: str
