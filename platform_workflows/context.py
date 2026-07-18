# Unified workflow runtime context.

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from platform_workflows.models import ExecutionStatus, StepResult


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
    memory: dict[str, Any] = field(default_factory=dict)
    fsm: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    step_results: dict[str, StepResult | dict[str, Any]] = field(default_factory=dict)
    plugin_id: str | None = None
    user_id: str | None = None
    input: dict[str, Any] = field(default_factory=dict)
    configuration: dict[str, Any] = field(default_factory=dict)
    conversation: dict[str, Any] = field(default_factory=dict)
    files: list[Any] = field(default_factory=list)
    history: list[Any] = field(default_factory=list)
    started_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)
    completed_at: datetime | None = None
    error: str | None = None
    cost_usd: float = 0.0

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
        input: dict[str, Any] | None = None,
        plugin_id: str | None = None,
        user_id: str | None = None,
    ) -> WorkflowContext:
        merged_vars = dict(variables or {})
        merged_input = dict(input or {})
        return cls(
            execution_id=str(uuid.uuid4()),
            workflow_id=workflow_id,
            vertical=vertical,
            current_step=current_step,
            status=ExecutionStatus.PENDING,
            telegram_user=dict(telegram_user or {}),
            variables=merged_vars,
            memory=dict(merged_vars),
            input=merged_input,
            metadata=dict(metadata or {}),
            plugin_id=plugin_id,
            user_id=user_id,
            configuration=dict(merged_input.get("configuration") or {}),
            conversation=dict(merged_input.get("conversation") or {}),
            files=list(merged_input.get("files") or []),
            history=list(merged_input.get("history") or []),
        )

    def touch(self) -> None:
        self.updated_at = _utcnow()

    def set_variable(self, key: str, value: Any) -> None:
        self.variables[key] = value
        self.memory[key] = value
        self.touch()

    def set_memory(self, key: str, value: Any) -> None:
        self.memory[key] = value
        self.variables[key] = value
        self.touch()

    def resolve(self, path: str) -> Any:
        if not path.startswith("$"):
            return self.memory.get(path)
        parts = path[1:].split(".")
        root = parts[0]
        mapping: dict[str, Any] = {
            "input": self.input,
            "memory": self.memory,
            "variables": self.variables,
            "request": self.request,
            "manager": self.manager,
            "telegram_user": self.telegram_user,
            "metadata": self.metadata,
            "fsm": self.fsm,
            "configuration": self.configuration,
        }
        current: Any = mapping.get(root, self.memory.get(root))
        for part in parts[1:]:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current

    def resolve_mapping(self, mapping: dict[str, Any]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, value in mapping.items():
            if isinstance(value, str) and value.startswith("$"):
                out[key] = self.resolve(value)
            elif isinstance(value, dict):
                out[key] = self.resolve_mapping(value)
            else:
                out[key] = value
        return out

    def get_step_output(self, step_id: str) -> Any:
        entry = self.step_results.get(step_id)
        if isinstance(entry, StepResult):
            return entry.output
        if isinstance(entry, dict):
            return entry.get("output")
        return None

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
            "memory": self.memory,
            "fsm": self.fsm,
            "metadata": self.metadata,
            "step_results": {
                k: (v.to_dict() if isinstance(v, StepResult) else v)
                for k, v in self.step_results.items()
            },
            "plugin_id": self.plugin_id,
            "user_id": self.user_id,
            "input": self.input,
            "configuration": self.configuration,
            "started_at": self.started_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "cost_usd": self.cost_usd,
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
            variables=dict(data.get("variables") or data.get("memory") or {}),
            memory=dict(data.get("memory") or data.get("variables") or {}),
            fsm=dict(data.get("fsm") or {}),
            metadata=dict(data.get("metadata") or {}),
            plugin_id=data.get("plugin_id"),
            user_id=data.get("user_id"),
            input=dict(data.get("input") or {}),
            configuration=dict(data.get("configuration") or {}),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else _utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else _utcnow(),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            error=data.get("error"),
            cost_usd=float(data.get("cost_usd") or 0.0),
        )
