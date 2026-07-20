# Planning domain models.

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PlanningStrategy(str, Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HIERARCHICAL = "hierarchical"
    GOAL_DECOMPOSITION = "goal_decomposition"
    DEPENDENCY_AWARE = "dependency_aware"
    ADAPTIVE_REPLANNING = "adaptive_replanning"


class PlanStepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PlanningContext:
    """Input context for plan generation."""

    goal: str
    agent_id: str | None = None
    user_id: str | None = None
    intent: str | None = None
    capabilities: list[str] = field(default_factory=list)
    available_tools: list[str] = field(default_factory=list)
    available_agents: list[str] = field(default_factory=list)
    memory_context: dict[str, Any] = field(default_factory=dict)
    reasoning_result: dict[str, Any] = field(default_factory=dict)
    constraints: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "goal": self.goal,
            "agent_id": self.agent_id,
            "user_id": self.user_id,
            "intent": self.intent,
            "capabilities": list(self.capabilities),
            "available_tools": list(self.available_tools),
            "available_agents": list(self.available_agents),
            "constraints": list(self.constraints),
            "permissions": list(self.permissions),
        }


@dataclass
class PlanStep:
    step_id: str
    name: str
    capability: str | None = None
    agent_id: str | None = None
    tool_id: str | None = None
    depends_on: list[str] = field(default_factory=list)
    parallel_group: str | None = None
    estimated_cost: float = 1.0
    status: PlanStepStatus = PlanStepStatus.PENDING
    output: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "name": self.name,
            "capability": self.capability,
            "agent_id": self.agent_id,
            "tool_id": self.tool_id,
            "depends_on": list(self.depends_on),
            "parallel_group": self.parallel_group,
            "estimated_cost": self.estimated_cost,
            "status": self.status.value,
        }


@dataclass
class PlanCandidate:
    candidate_id: str
    strategy: PlanningStrategy
    steps: list[PlanStep]
    estimated_cost: float = 0.0
    estimated_duration_ms: float = 0.0
    score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "strategy": self.strategy.value,
            "step_count": len(self.steps),
            "estimated_cost": self.estimated_cost,
            "score": self.score,
        }


@dataclass
class ExecutionPlan:
    plan_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    goal: str = ""
    strategy: PlanningStrategy = PlanningStrategy.DEPENDENCY_AWARE
    steps: list[PlanStep] = field(default_factory=list)
    estimated_cost: float = 0.0
    status: str = "draft"
    created_at: float = field(default_factory=time.time)
    completed_steps: list[str] = field(default_factory=list)
    failed_step_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def step_count(self) -> int:
        return len(self.steps)

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "goal": self.goal,
            "strategy": self.strategy.value,
            "steps": [s.to_dict() for s in self.steps],
            "estimated_cost": self.estimated_cost,
            "status": self.status,
            "completed_steps": list(self.completed_steps),
        }


@dataclass
class PlanningResult:
    plan: ExecutionPlan
    candidates: list[PlanCandidate] = field(default_factory=list)
    validation_passed: bool = True
    validation_errors: list[str] = field(default_factory=list)
    workflow_definition: dict[str, Any] = field(default_factory=dict)
    planning_time_ms: float = 0.0
    success: bool = True
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan": self.plan.to_dict(),
            "candidates": [c.to_dict() for c in self.candidates],
            "validation_passed": self.validation_passed,
            "validation_errors": list(self.validation_errors),
            "workflow_definition": dict(self.workflow_definition),
            "planning_time_ms": self.planning_time_ms,
            "success": self.success,
        }
