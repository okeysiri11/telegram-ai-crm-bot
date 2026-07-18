# WorkflowContext — runtime state for workflow executions.

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from workflow.models import ExecutionStatus


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class WorkflowContext:
    execution_id: str
    workflow_id: str
    vertical: str
    current_step: str | None
    status: ExecutionStatus
    telegram_user: dict[str, Any] = field(default_factory=dict)
    request: dict[str, Any] = field(default_factory=dict)
    manager: dict[str, Any] = field(default_factory=dict)
    variables: dict[str, Any] = field(default_factory=dict)
    fsm: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    started_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)
    completed_at: datetime | None = None
    error: str | None = None

    @classmethod
    def create(
        cls,
        *,
        workflow_id: str,
        vertical: str,
        telegram_user: dict[str, Any] | None = None,
        variables: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        current_step: str | None = None,
    ) -> WorkflowContext:
        return cls(
            execution_id=str(uuid.uuid4()),
            workflow_id=workflow_id,
            vertical=vertical,
            current_step=current_step,
            status=ExecutionStatus.PENDING,
            telegram_user=dict(telegram_user or {}),
            variables=dict(variables or {}),
            metadata=dict(metadata or {}),
        )

    def touch(self) -> None:
        self.updated_at = _utcnow()

    def set_variable(self, key: str, value: Any) -> None:
        self.variables[key] = value
        self.touch()

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "vertical": self.vertical,
            "current_step": self.current_step,
            "status": self.status.value,
            "telegram_user": self.telegram_user,
            "request": self.request,
            "manager": self.manager,
            "variables": self.variables,
            "fsm": self.fsm,
            "metadata": self.metadata,
            "started_at": self.started_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkflowContext:
        return cls(
            execution_id=str(data["execution_id"]),
            workflow_id=str(data["workflow_id"]),
            vertical=str(data.get("vertical") or ""),
            current_step=data.get("current_step"),
            status=ExecutionStatus(data.get("status") or ExecutionStatus.PENDING.value),
            telegram_user=dict(data.get("telegram_user") or {}),
            request=dict(data.get("request") or {}),
            manager=dict(data.get("manager") or {}),
            variables=dict(data.get("variables") or {}),
            fsm=dict(data.get("fsm") or {}),
            metadata=dict(data.get("metadata") or {}),
            started_at=datetime.fromisoformat(data["started_at"])
            if data.get("started_at")
            else _utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"])
            if data.get("updated_at")
            else _utcnow(),
            completed_at=datetime.fromisoformat(data["completed_at"])
            if data.get("completed_at")
            else None,
            error=data.get("error"),
        )
