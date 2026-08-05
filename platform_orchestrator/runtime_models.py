"""Multi-Agent Runtime models — Sprint 36.7 (extends platform_orchestrator SoR)."""

from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class CollaborationMode(str, Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HIERARCHICAL = "hierarchical"
    SWARM = "swarm"
    SUPERVISOR_WORKER = "supervisor_worker"


class PlanStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RuntimeTaskStatus(str, Enum):
    QUEUED = "queued"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    CHECKPOINTED = "checkpointed"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    RETRYING = "retrying"


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


@dataclass
class AgentRecord:
    agent_id: str
    name: str
    description: str = ""
    capabilities: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    availability: str = "available"  # available | busy | offline
    healthy: bool = True
    priority: int = 50
    version: str = "1.0.0"
    metadata: dict[str, Any] = field(default_factory=dict)
    last_health_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AgentSession:
    session_id: str
    goal: str
    mode: CollaborationMode | str = CollaborationMode.SEQUENTIAL
    status: str = "active"
    agent_ids: list[str] = field(default_factory=list)
    shared_context: dict[str, Any] = field(default_factory=dict)
    shared_memory: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.mode, str):
            self.mode = CollaborationMode(self.mode)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "goal": self.goal,
            "mode": self.mode.value if isinstance(self.mode, CollaborationMode) else self.mode,
            "status": self.status,
            "agent_ids": list(self.agent_ids),
            "shared_context": dict(self.shared_context),
            "shared_memory": dict(self.shared_memory),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": dict(self.metadata),
        }


@dataclass
class PlanStep:
    step_id: str
    title: str
    capability: str
    agent_id: str | None = None
    depends_on: list[str] = field(default_factory=list)
    payload: dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    result: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AgentPlan:
    plan_id: str
    session_id: str | None
    goal: str
    mode: CollaborationMode | str
    steps: list[PlanStep] = field(default_factory=list)
    status: PlanStatus | str = PlanStatus.DRAFT
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if isinstance(self.mode, str):
            self.mode = CollaborationMode(self.mode)
        if isinstance(self.status, str):
            self.status = PlanStatus(self.status)

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "session_id": self.session_id,
            "goal": self.goal,
            "mode": self.mode.value if isinstance(self.mode, CollaborationMode) else self.mode,
            "steps": [s.to_dict() for s in self.steps],
            "status": self.status.value if isinstance(self.status, PlanStatus) else self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class RuntimeTask:
    task_id: str
    title: str
    capability: str
    status: RuntimeTaskStatus | str = RuntimeTaskStatus.QUEUED
    agent_id: str | None = None
    session_id: str | None = None
    plan_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    retries: int = 0
    max_retries: int = 2
    timeout_sec: float = 30.0
    checkpoint: dict[str, Any] = field(default_factory=dict)
    schedule_at: float | None = None
    result: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if isinstance(self.status, str):
            self.status = RuntimeTaskStatus(self.status)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "capability": self.capability,
            "status": self.status.value if isinstance(self.status, RuntimeTaskStatus) else self.status,
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "plan_id": self.plan_id,
            "payload": dict(self.payload),
            "retries": self.retries,
            "max_retries": self.max_retries,
            "timeout_sec": self.timeout_sec,
            "checkpoint": dict(self.checkpoint),
            "schedule_at": self.schedule_at,
            "result": dict(self.result),
            "error": self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class AgentCommMessage:
    message_id: str
    channel: str  # direct | pubsub | event
    source_agent_id: str
    target_agent_id: str | None = None
    topic: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExecutionRecord:
    execution_id: str
    session_id: str | None
    plan_id: str | None
    mode: str
    status: str
    results: list[dict[str, Any]] = field(default_factory=list)
    aggregated: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    finished_at: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
