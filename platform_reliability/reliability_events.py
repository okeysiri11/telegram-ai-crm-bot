# Reliability lifecycle events.

from __future__ import annotations

from dataclasses import dataclass

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class RecoveryStartedEvent(BaseEvent):
    execution_id: str
    component: str
    workflow_id: str | None = None


@dataclass(kw_only=True)
class RecoveryCompletedEvent(BaseEvent):
    execution_id: str
    success: bool
    action: str
    recovery_time_ms: float = 0.0


@dataclass(kw_only=True)
class CircuitStateChangedEvent(BaseEvent):
    circuit_id: str
    new_state: str
    failure_count: int = 0


@dataclass(kw_only=True)
class CheckpointSavedEvent(BaseEvent):
    checkpoint_id: str
    workflow_id: str | None = None
    task_id: str | None = None


@dataclass(kw_only=True)
class FailoverTriggeredEvent(BaseEvent):
    execution_id: str
    primary: str
    fallback: str
    component: str = "agent"
