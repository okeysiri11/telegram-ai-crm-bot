# AI Workflow domain models.

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class StepType(str, Enum):
    SKILL = "skill"
    CONDITION = "condition"
    BRANCH = "branch"
    LOOP = "loop"
    TRANSFORM = "transform"
    MERGE = "merge"
    PARALLEL = "parallel"
    APPROVAL = "approval"
    PLUGIN = "plugin"
    DELAY = "delay"
    EVENT = "event"


class WorkflowState(str, Enum):
    REGISTERED = "registered"
    LOADED = "loaded"
    DISABLED = "disabled"


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowStep:
    step_id: str
    step_type: str
    config: dict[str, Any] = field(default_factory=dict)
    next: str | None = None
    on_true: str | None = None
    on_false: str | None = None
    fallback: str | None = None
    branches: list[str] = field(default_factory=list)
    retries: int = 0
    timeout_seconds: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "step_type": self.step_type,
            "config": self.config,
            "next": self.next,
            "on_true": self.on_true,
            "on_false": self.on_false,
            "fallback": self.fallback,
            "branches": self.branches,
            "retries": self.retries,
            "timeout_seconds": self.timeout_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkflowStep:
        return cls(
            step_id=data["step_id"],
            step_type=data["step_type"],
            config=data.get("config", {}),
            next=data.get("next"),
            on_true=data.get("on_true"),
            on_false=data.get("on_false"),
            fallback=data.get("fallback"),
            branches=data.get("branches", []),
            retries=int(data.get("retries", 0)),
            timeout_seconds=data.get("timeout_seconds"),
        )


@dataclass
class WorkflowDefinition:
    workflow_id: str
    name: str
    entry_step: str
    steps: dict[str, WorkflowStep]
    version: str = "1.0.0"
    description: str = ""
    tags: list[str] = field(default_factory=list)
    category: str = "general"
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "entry_step": self.entry_step,
            "tags": self.tags,
            "category": self.category,
            "enabled": self.enabled,
            "steps": {k: v.to_dict() for k, v in self.steps.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkflowDefinition:
        steps = {s["step_id"]: WorkflowStep.from_dict(s) for s in data.get("steps", [])}
        return cls(
            workflow_id=data["workflow_id"],
            name=data.get("name", data["workflow_id"]),
            entry_step=data["entry_step"],
            steps=steps,
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            tags=data.get("tags", []),
            category=data.get("category", "general"),
            enabled=data.get("enabled", True),
        )


@dataclass
class WorkflowRecord:
    definition: WorkflowDefinition
    state: WorkflowState = WorkflowState.REGISTERED
    loaded_at: str | None = None

    @property
    def workflow_id(self) -> str:
        return self.definition.workflow_id

    def to_dict(self) -> dict[str, Any]:
        return {**self.definition.to_dict(), "state": self.state.value, "loaded_at": self.loaded_at}


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


@dataclass
class WorkflowExecutionState:
    execution_id: str
    workflow_id: str
    status: ExecutionStatus
    current_step: str | None = None
    input: dict[str, Any] = field(default_factory=dict)
    memory: dict[str, Any] = field(default_factory=dict)
    step_results: dict[str, StepResult] = field(default_factory=dict)
    plugin_id: str | None = None
    user_id: str | None = None
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: str | None = None
    error: str | None = None
    cost_usd: float = 0.0
    cancelled: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "status": self.status.value,
            "current_step": self.current_step,
            "input": self.input,
            "memory": self.memory,
            "step_results": {k: v.to_dict() for k, v in self.step_results.items()},
            "plugin_id": self.plugin_id,
            "user_id": self.user_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error": self.error,
            "cost_usd": self.cost_usd,
        }
