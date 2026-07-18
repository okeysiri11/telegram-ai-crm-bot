# Workflow definition models — step types and parsed workflow structure.

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any


class StepType(str, enum.Enum):
    CALLBACK = "callback"
    INPUT = "input"
    QUESTION = "question"
    CHOICE = "choice"
    MEDIA = "media"
    CONDITION = "condition"
    SERVICE = "service"
    EVENT = "event"
    DELAY = "delay"
    COMPLETE = "complete"


class ExecutionStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class StepDefinition:
    id: str
    type: StepType
    config: dict[str, Any] = field(default_factory=dict)
    next_step: str | None = None

    @property
    def is_interactive(self) -> bool:
        return self.type in {
            StepType.CALLBACK,
            StepType.INPUT,
            StepType.QUESTION,
            StepType.CHOICE,
            StepType.MEDIA,
        }


@dataclass(frozen=True)
class WorkflowDefinition:
    id: str
    vertical: str
    description: str = ""
    steps: list[StepDefinition] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def step_by_id(self, step_id: str) -> StepDefinition | None:
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def first_step(self) -> StepDefinition | None:
        return self.steps[0] if self.steps else None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "vertical": self.vertical,
            "description": self.description,
            "metadata": self.metadata,
            "steps": [
                {
                    "id": s.id,
                    "type": s.type.value,
                    "config": s.config,
                    "next_step": s.next_step,
                }
                for s in self.steps
            ],
        }
