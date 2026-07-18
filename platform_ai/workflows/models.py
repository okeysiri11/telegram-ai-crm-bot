# AI workflow models — compatibility facade over unified platform_workflows models.

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from platform_workflows.models import (
    ExecutionStatus as UnifiedExecutionStatus,
    StepDefinition,
    StepResult,
    StepType as UnifiedStepType,
    WorkflowDefinition as UnifiedWorkflowDefinition,
    WorkflowExecutionRequest,
    WorkflowExecutionResult,
)


class StepType(str, Enum):
    SKILL = UnifiedStepType.SKILL.value
    CONDITION = UnifiedStepType.CONDITION.value
    BRANCH = UnifiedStepType.BRANCH.value
    LOOP = UnifiedStepType.LOOP.value
    TRANSFORM = UnifiedStepType.TRANSFORM.value
    MERGE = UnifiedStepType.MERGE.value
    PARALLEL = UnifiedStepType.PARALLEL.value
    APPROVAL = UnifiedStepType.APPROVAL.value
    PLUGIN = UnifiedStepType.PLUGIN.value
    DELAY = UnifiedStepType.DELAY.value
    EVENT = UnifiedStepType.EVENT.value


class WorkflowState(str, Enum):
    REGISTERED = "registered"
    LOADED = "loaded"
    DISABLED = "disabled"


class ExecutionStatus(str, Enum):
    PENDING = UnifiedExecutionStatus.PENDING.value.lower()
    RUNNING = UnifiedExecutionStatus.RUNNING.value.lower()
    PAUSED = UnifiedExecutionStatus.PAUSED.value.lower()
    COMPLETED = UnifiedExecutionStatus.COMPLETED.value.lower()
    FAILED = UnifiedExecutionStatus.FAILED.value.lower()
    CANCELLED = UnifiedExecutionStatus.CANCELLED.value.lower()



def make_workflow_step(step_id: str, step_type: str, **kwargs: Any) -> StepDefinition:
    return StepDefinition.from_dict({"step_id": step_id, "step_type": step_type, **kwargs}, step_id=step_id)


# Tests and legacy code construct steps with step_id= keyword.
WorkflowStep = make_workflow_step  # type: ignore[misc,assignment]


@dataclass
class WorkflowDefinition:
    workflow_id: str
    name: str
    entry_step: str
    steps: dict[str, StepDefinition]
    version: str = "1.0.0"
    description: str = ""
    tags: list[str] = field(default_factory=list)
    category: str = "general"
    enabled: bool = True

    def to_unified(self) -> UnifiedWorkflowDefinition:
        return UnifiedWorkflowDefinition(
            id=self.workflow_id,
            vertical=self.category.upper(),
            description=self.description or self.name,
            steps=dict(self.steps),
            entry_step=self.entry_step,
            version=self.version,
            category=self.category,
            tags=list(self.tags),
            enabled=self.enabled,
            metadata={"name": self.name},
        )

    def to_dict(self) -> dict[str, Any]:
        return self.to_unified().to_dict()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkflowDefinition:
        wf_id = data.get("workflow_id") or data.get("id")
        if not wf_id:
            raise KeyError("workflow_id")
        raw_steps = data.get("steps") or {}
        if isinstance(raw_steps, list):
            steps = {
                str(s.get("step_id") or s.get("id")): StepDefinition.from_dict(
                    s, step_id=str(s.get("step_id") or s.get("id"))
                )
                for s in raw_steps
            }
        else:
            steps = {k: StepDefinition.from_dict(v, step_id=k) for k, v in raw_steps.items()}
        return cls(
            workflow_id=str(wf_id),
            name=data.get("name", wf_id),
            entry_step=data["entry_step"],
            steps=steps,
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            tags=list(data.get("tags") or []),
            category=data.get("category", "general"),
            enabled=bool(data.get("enabled", True)),
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
    started_at: str = ""
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


__all__ = [
    "ExecutionStatus",
    "StepResult",
    "StepType",
    "WorkflowDefinition",
    "WorkflowExecutionRequest",
    "WorkflowExecutionResult",
    "WorkflowExecutionState",
    "WorkflowRecord",
    "WorkflowState",
    "WorkflowStep",
]
