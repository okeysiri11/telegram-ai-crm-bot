# Workflow & task lifecycle events — integrated with PlatformEventBus.

from __future__ import annotations

from dataclasses import dataclass

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class TaskCreatedEvent(BaseEvent):
    task_id: str
    workflow_id: str
    task_type: str
    capability: str | None = None


@dataclass(kw_only=True)
class TaskAssignedEvent(BaseEvent):
    task_id: str
    workflow_id: str
    assignee_id: str
    assignee_type: str


@dataclass(kw_only=True)
class TaskStartedEvent(BaseEvent):
    task_id: str
    workflow_id: str
    assignee_id: str | None = None


@dataclass(kw_only=True)
class TaskCompletedEvent(BaseEvent):
    task_id: str
    workflow_id: str
    execution_time_ms: float = 0.0


@dataclass(kw_only=True)
class TaskFailedEvent(BaseEvent):
    task_id: str
    workflow_id: str
    error: str
    retries: int = 0


@dataclass(kw_only=True)
class WorkflowCompletedEvent(BaseEvent):
    workflow_id: str
    name: str
    task_count: int = 0


@dataclass(kw_only=True)
class WorkflowFailedEvent(BaseEvent):
    workflow_id: str
    name: str
    error: str
    failed_task_id: str | None = None
