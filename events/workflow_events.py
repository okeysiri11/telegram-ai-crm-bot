# Workflow lifecycle events for the platform EventBus.

from __future__ import annotations

from dataclasses import dataclass

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class WorkflowStartedEvent(BaseEvent):
    execution_id: str
    workflow_id: str
    vertical: str
    telegram_user_id: int | None = None
    current_step: str | None = None


@dataclass(kw_only=True)
class WorkflowStepCompletedEvent(BaseEvent):
    execution_id: str
    workflow_id: str
    step_id: str
    step_type: str
    duration_ms: float = 0.0
    status: str = "RUNNING"


@dataclass(kw_only=True)
class WorkflowCompletedEvent(BaseEvent):
    execution_id: str
    workflow_id: str
    vertical: str
    duration_ms: float = 0.0
    request_number: str | None = None


@dataclass(kw_only=True)
class WorkflowCancelledEvent(BaseEvent):
    execution_id: str
    workflow_id: str
    vertical: str
    reason: str = "cancelled"
    current_step: str | None = None
