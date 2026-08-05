"""Workflow Runtime domain models — Sprint 36.2 (extends platform_workflow SoR)."""

from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class RegistryStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"
    ROLLING_BACK = "rolling_back"
    ROLLED_BACK = "rolled_back"
    SCHEDULED = "scheduled"


class StepKind(str, Enum):
    START = "start"
    END = "end"
    TASK = "task"
    CONDITION = "condition"
    LOOP = "loop"
    PARALLEL = "parallel"
    DELAY = "delay"
    SET_VARIABLE = "set_variable"
    EXPRESSIONS = "expression"
    ROLLBACK = "rollback"
    SUBWORKFLOW = "subworkflow"


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


@dataclass
class GraphStep:
    step_id: str
    name: str
    kind: StepKind | str = StepKind.TASK
    next: list[str] = field(default_factory=list)
    # condition: expression -> branch step ids
    when_true: str | None = None
    when_false: str | None = None
    condition: str | None = None
    # loop
    loop_over: str | None = None  # variable name
    loop_body: str | None = None  # step id to enter
    max_iterations: int = 10
    # parallel
    branches: list[str] = field(default_factory=list)
    join: str | None = None
    # task / expression
    action: str | None = None
    expression: str | None = None
    set_var: str | None = None
    value: Any = None
    delay_sec: float = 0.0
    compensate: str | None = None  # rollback step id
    timeout_sec: float = 30.0
    max_retries: int = 2
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.kind, str):
            self.kind = StepKind(self.kind)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["kind"] = self.kind.value if isinstance(self.kind, StepKind) else self.kind
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GraphStep:
        return cls(
            step_id=str(data.get("step_id") or f"step_{uuid.uuid4().hex[:8]}"),
            name=str(data.get("name") or "step"),
            kind=data.get("kind") or StepKind.TASK,
            next=list(data.get("next") or []),
            when_true=data.get("when_true"),
            when_false=data.get("when_false"),
            condition=data.get("condition"),
            loop_over=data.get("loop_over"),
            loop_body=data.get("loop_body"),
            max_iterations=int(data.get("max_iterations") or 10),
            branches=list(data.get("branches") or []),
            join=data.get("join"),
            action=data.get("action"),
            expression=data.get("expression"),
            set_var=data.get("set_var"),
            value=data.get("value"),
            delay_sec=float(data.get("delay_sec") or 0),
            compensate=data.get("compensate"),
            timeout_sec=float(data.get("timeout_sec") or 30),
            max_retries=int(data.get("max_retries") or 2),
            metadata=dict(data.get("metadata") or {}),
        )


@dataclass
class WorkflowDefinition:
    workflow_id: str
    name: str
    version: str = "1.0.0"
    description: str = ""
    status: RegistryStatus | str = RegistryStatus.DRAFT
    steps: list[GraphStep] = field(default_factory=list)
    start_step: str | None = None
    owner: str = "platform"
    tags: list[str] = field(default_factory=list)
    variables: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    published_at: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.status, str):
            self.status = RegistryStatus(self.status)
        if not self.start_step and self.steps:
            starts = [s for s in self.steps if s.kind == StepKind.START]
            self.start_step = starts[0].step_id if starts else self.steps[0].step_id

    def step_map(self) -> dict[str, GraphStep]:
        return {s.step_id: s for s in self.steps}

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "status": self.status.value if isinstance(self.status, RegistryStatus) else self.status,
            "steps": [s.to_dict() for s in self.steps],
            "start_step": self.start_step,
            "owner": self.owner,
            "tags": list(self.tags),
            "variables": dict(self.variables),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "published_at": self.published_at,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkflowDefinition:
        steps = [GraphStep.from_dict(s) for s in (data.get("steps") or [])]
        return cls(
            workflow_id=str(data.get("workflow_id") or f"wf_{uuid.uuid4().hex[:12]}"),
            name=str(data.get("name") or "unnamed"),
            version=str(data.get("version") or "1.0.0"),
            description=str(data.get("description") or ""),
            status=data.get("status") or RegistryStatus.DRAFT,
            steps=steps,
            start_step=data.get("start_step"),
            owner=str(data.get("owner") or "platform"),
            tags=list(data.get("tags") or []),
            variables=dict(data.get("variables") or {}),
            created_at=float(data.get("created_at") or time.time()),
            updated_at=float(data.get("updated_at") or time.time()),
            published_at=data.get("published_at"),
            metadata=dict(data.get("metadata") or {}),
        )


@dataclass
class WorkflowVersionRecord:
    workflow_id: str
    version: str
    snapshot: dict[str, Any]
    changelog: str = ""
    created_at: float = field(default_factory=time.time)
    created_by: str = "system"
    is_active: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RuntimeContext:
    vars: dict[str, Any] = field(default_factory=dict)
    memory: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    temp: dict[str, Any] = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> RuntimeContext:
        data = data or {}
        return cls(
            vars=dict(data.get("vars") or {}),
            memory=dict(data.get("memory") or {}),
            outputs=dict(data.get("outputs") or {}),
            temp=dict(data.get("temp") or {}),
            meta=dict(data.get("meta") or {}),
        )


@dataclass
class StepRunRecord:
    step_id: str
    name: str
    kind: str
    status: StepStatus | str = StepStatus.PENDING
    attempt: int = 0
    started_at: float | None = None
    finished_at: float | None = None
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    duration_ms: float | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value if isinstance(self.status, StepStatus) else self.status
        return d


@dataclass
class WorkflowRun:
    run_id: str
    workflow_id: str
    version: str
    status: RunStatus | str = RunStatus.PENDING
    mode: str = "sync"  # sync | async | scheduled
    context: RuntimeContext = field(default_factory=RuntimeContext)
    steps: list[StepRunRecord] = field(default_factory=list)
    checkpoints: list[dict[str, Any]] = field(default_factory=list)
    logs: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None
    scheduled_at: float | None = None
    started_at: float | None = None
    finished_at: float | None = None
    timeout_sec: float = 120.0
    rollback_of: str | None = None
    created_at: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if isinstance(self.status, str):
            self.status = RunStatus(self.status)
        if isinstance(self.context, dict):
            self.context = RuntimeContext.from_dict(self.context)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "workflow_id": self.workflow_id,
            "version": self.version,
            "status": self.status.value if isinstance(self.status, RunStatus) else self.status,
            "mode": self.mode,
            "context": self.context.to_dict(),
            "steps": [s.to_dict() for s in self.steps],
            "checkpoints": list(self.checkpoints),
            "logs": list(self.logs[-100:]),
            "error": self.error,
            "scheduled_at": self.scheduled_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "timeout_sec": self.timeout_sec,
            "rollback_of": self.rollback_of,
            "created_at": self.created_at,
        }


def eval_expression(expr: str, ctx: RuntimeContext) -> Any:
    """Safe-ish expression eval over vars/outputs/memory/temp/meta."""
    expr = (expr or "").strip()
    if not expr:
        return None

    class _Attr(dict):
        def __getattr__(self, item: str) -> Any:
            try:
                return self[item]
            except KeyError as exc:
                raise AttributeError(item) from exc

    env = {
        "vars": _Attr(ctx.vars),
        "outputs": _Attr(ctx.outputs),
        "memory": _Attr(ctx.memory),
        "temp": _Attr(ctx.temp),
        "meta": _Attr(ctx.meta),
        "true": True,
        "false": False,
        "null": None,
    }
    for k, v in ctx.vars.items():
        if str(k).isidentifier() and k not in env:
            env[k] = v
    try:
        return eval(expr, {"__builtins__": {}}, env)  # noqa: S307 — controlled sandbox
    except Exception:
        if expr.startswith("vars."):
            key = expr.split(".", 1)[1]
            return ctx.vars.get(key)
        return bool(ctx.vars.get(expr))
