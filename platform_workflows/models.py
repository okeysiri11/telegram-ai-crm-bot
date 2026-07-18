# Unified workflow models — YAML, Python, and AI step graphs.

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


class StepType(str, enum.Enum):
    CALLBACK = "callback"
    INPUT = "input"
    QUESTION = "question"
    CHOICE = "choice"
    MEDIA = "media"
    CONDITION = "condition"
    BRANCH = "branch"
    LOOP = "loop"
    PARALLEL = "parallel"
    SERVICE = "service"
    EVENT = "event"
    DELAY = "delay"
    SKILL = "skill"
    AI = "ai"
    TRANSFORM = "transform"
    MERGE = "merge"
    APPROVAL = "approval"
    PLUGIN = "plugin"
    COMPLETE = "complete"


class ExecutionStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class StepDefinition:
    id: str
    type: StepType
    config: dict[str, Any] = field(default_factory=dict)
    next_step: str | None = None
    on_true: str | None = None
    on_false: str | None = None
    fallback: str | None = None
    branches: list[str] = field(default_factory=list)
    retries: int = 0
    timeout_seconds: float | None = None

    @property
    def is_interactive(self) -> bool:
        return self.type in {
            StepType.CALLBACK,
            StepType.INPUT,
            StepType.QUESTION,
            StepType.CHOICE,
            StepType.MEDIA,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "step_id": self.id,
            "type": self.type.value,
            "step_type": self.type.value,
            "config": self.config,
            "next_step": self.next_step,
            "next": self.next_step,
            "on_true": self.on_true,
            "on_false": self.on_false,
            "fallback": self.fallback,
            "branches": list(self.branches),
            "retries": self.retries,
            "timeout_seconds": self.timeout_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], *, step_id: str | None = None) -> StepDefinition:
        sid = step_id or str(data.get("id") or data.get("step_id") or "")
        raw_type = str(data.get("type") or data.get("step_type") or "complete").lower()
        if raw_type == "ai":
            raw_type = "skill"
        step_type = StepType(raw_type)
        config = dict(data.get("config") or {})
        for key in (
            "id",
            "step_id",
            "type",
            "step_type",
            "config",
            "next",
            "next_step",
            "on_true",
            "on_false",
            "fallback",
            "branches",
            "retries",
            "timeout_seconds",
        ):
            if key in data and key not in config and key not in {"id", "step_id", "type", "step_type", "config"}:
                if key in {"next", "next_step"}:
                    continue
                if key in data and key not in config:
                    pass
        for k, v in data.items():
            if k not in {
                "id",
                "step_id",
                "type",
                "step_type",
                "config",
                "next",
                "next_step",
                "on_true",
                "on_false",
                "fallback",
                "branches",
                "retries",
                "timeout_seconds",
            }:
                config.setdefault(k, v)
        return cls(
            id=sid,
            type=step_type,
            config=config,
            next_step=data.get("next_step") or data.get("next"),
            on_true=data.get("on_true") or data.get("then"),
            on_false=data.get("on_false") or data.get("else"),
            fallback=data.get("fallback"),
            branches=list(data.get("branches") or []),
            retries=int(data.get("retries") or 0),
            timeout_seconds=data.get("timeout_seconds"),
        )


@dataclass(frozen=True)
class WorkflowDefinition:
    id: str
    vertical: str
    description: str = ""
    steps: dict[str, StepDefinition] = field(default_factory=dict)
    entry_step: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    version: str = "1.0.0"
    category: str = "general"
    tags: list[str] = field(default_factory=list)
    enabled: bool = True

    @classmethod
    def from_list_steps(
        cls,
        *,
        workflow_id: str,
        vertical: str,
        steps: list[StepDefinition],
        **kwargs: Any,
    ) -> WorkflowDefinition:
        step_map = {s.id: s for s in steps}
        entry = steps[0].id if steps else None
        return cls(id=workflow_id, vertical=vertical, steps=step_map, entry_step=entry, **kwargs)

    def step_by_id(self, step_id: str) -> StepDefinition | None:
        return self.steps.get(step_id)

    def first_step(self) -> StepDefinition | None:
        if self.entry_step:
            return self.steps.get(self.entry_step)
        if self.steps:
            return next(iter(self.steps.values()))
        return None

    def step_list(self) -> list[StepDefinition]:
        return list(self.steps.values())

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "workflow_id": self.id,
            "vertical": self.vertical,
            "description": self.description,
            "entry_step": self.entry_step,
            "metadata": self.metadata,
            "version": self.version,
            "category": self.category,
            "tags": self.tags,
            "enabled": self.enabled,
            "steps": {k: v.to_dict() for k, v in self.steps.items()},
        }


@dataclass
class StepResult:
    step_id: str
    step_type: str
    success: bool
    output: dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "step_type": self.step_type,
            "success": self.success,
            "output": self.output,
            "latency_ms": self.latency_ms,
            "cost_usd": self.cost_usd,
            "error": self.error,
        }


@dataclass
class WorkflowExecutionRequest:
    workflow_id: str
    input: dict[str, Any] = field(default_factory=dict)
    plugin_id: str | None = None
    user_id: str | None = None
    use_cache: bool = True
    execution_id: str = field(default_factory=lambda: str(uuid4()))
    vertical: str | None = None
    telegram_user: dict[str, Any] | None = None
    request: dict[str, Any] | None = None
    manager: dict[str, Any] | None = None
    variables: dict[str, Any] | None = None


@dataclass
class WorkflowExecutionResult:
    execution_id: str
    workflow_id: str
    status: str
    output: dict[str, Any] = field(default_factory=dict)
    step_results: list[StepResult] = field(default_factory=list)
    memory: dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    cached: bool = False
    current_step: str | None = None
    error: str | None = None
    context: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "status": self.status,
            "output": self.output,
            "step_results": [s.to_dict() for s in self.step_results],
            "memory": self.memory,
            "latency_ms": self.latency_ms,
            "cost_usd": self.cost_usd,
            "cached": self.cached,
            "current_step": self.current_step,
            "error": self.error,
        }


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
