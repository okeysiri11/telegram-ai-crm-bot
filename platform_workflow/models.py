# Core workflow and task domain models.

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TaskStatus(str, Enum):
    NEW = "new"
    QUEUED = "queued"
    ASSIGNED = "assigned"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(int, Enum):
    LOW = 4
    NORMAL = 3
    HIGH = 2
    URGENT = 1


class TaskType(str, Enum):
    AGENT = "agent"
    HUMAN = "human"
    SYSTEM = "system"
    HYBRID = "hybrid"


class WorkflowStatus(str, Enum):
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class HumanRole(str, Enum):
    MANAGER = "manager"
    ADMINISTRATOR = "administrator"
    OPERATOR = "operator"
    OWNER = "owner"


@dataclass
class ExecutionContext:
    """Runtime context passed through workflow execution."""

    user_id: str | None = None
    session_id: str | None = None
    tenant_id: str | None = None
    telegram_user_id: str | None = None
    permissions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "tenant_id": self.tenant_id,
            "telegram_user_id": self.telegram_user_id,
            "permissions": list(self.permissions),
            "metadata": dict(self.metadata),
        }


@dataclass
class WorkflowStep:
    step_id: str
    name: str
    capability: str | None = None
    task_type: TaskType = TaskType.AGENT
    human_role: HumanRole | None = None
    assignee_id: str | None = None
    depends_on: list[str] = field(default_factory=list)
    max_retries: int = 3
    timeout_seconds: float = 300.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Workflow:
    workflow_id: str
    name: str
    description: str = ""
    steps: list[WorkflowStep] = field(default_factory=list)
    status: WorkflowStatus = WorkflowStatus.DRAFT
    context: ExecutionContext = field(default_factory=ExecutionContext)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        name: str,
        steps: list[WorkflowStep],
        *,
        description: str = "",
        context: ExecutionContext | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Workflow:
        return cls(
            workflow_id=str(uuid.uuid4()),
            name=name,
            description=description,
            steps=steps,
            context=context or ExecutionContext(),
            metadata=metadata or {},
        )


@dataclass
class Task:
    task_id: str
    workflow_id: str
    step_id: str
    task_type: TaskType
    status: TaskStatus = TaskStatus.NEW
    priority: TaskPriority = TaskPriority.NORMAL
    capability: str | None = None
    assignee_id: str | None = None
    assignee_type: str | None = None  # agent | human
    human_role: HumanRole | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    result: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    retry_count: int = 0
    max_retries: int = 3
    scheduled_at: float | None = None
    run_at: float | None = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    completed_at: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_step(cls, workflow: Workflow, step: WorkflowStep) -> Task:
        return cls(
            task_id=str(uuid.uuid4()),
            workflow_id=workflow.workflow_id,
            step_id=step.step_id,
            task_type=step.task_type,
            capability=step.capability,
            human_role=step.human_role,
            assignee_id=step.assignee_id,
            max_retries=step.max_retries,
            payload=dict(step.metadata),
            metadata={"step_name": step.name},
        )


@dataclass
class TaskResult:
    task_id: str
    workflow_id: str
    success: bool
    status: TaskStatus
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    execution_time_ms: float = 0.0
    assignee_id: str | None = None
    retries: int = 0
