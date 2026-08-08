"""Hercules core models — ExecutionContext, Plan, Graph, State, Lifecycle."""

from __future__ import annotations

import enum
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


class TaskLifecycle(str, enum.Enum):
    CREATED = "создана"
    QUEUED = "в_очереди"
    SCHEDULED = "запланирована"
    RUNNING = "выполняется"
    WAITING = "ожидает"
    SUCCEEDED = "успех"
    FAILED = "ошибка"
    RETRYING = "повтор"
    CANCELLED = "отменена"
    TIMEOUT = "таймаут"


class QueueKind(str, enum.Enum):
    TASK = "task"
    AI = "ai"
    IMAGE = "image"
    VIDEO = "video"
    VOICE = "voice"
    WORKFLOW = "workflow"
    NOTIFICATION = "notification"
    TELEGRAM = "telegram"
    PUBLISH = "publish"
    BACKGROUND = "background"
    GPU = "gpu"
    CPU = "cpu"
    DELAYED = "delayed"
    RETRY = "retry"
    REALTIME = "realtime"
    SCHEDULED = "scheduled"


class ExecutorBackend(str, enum.Enum):
    PYTHON = "python"
    NODE = "node"
    AI_PROVIDER = "ai_provider"
    HTTP = "http"
    REST = "rest"
    WEBSOCKET = "websocket"
    N8N = "n8n"
    TELEGRAM = "telegram"
    INTERNAL = "internal"
    CRON = "cron"
    EVENT_BUS = "event_bus"
    WORKFLOW = "workflow"
    PIPELINE = "pipeline"


@dataclass
class ExecutionContext:
    owner_id: str
    tenant_id: str | None = None
    channel: str = "internal"  # telegram|desktop|api|agent|workflow
    vertical: str | None = None
    session_id: str | None = None
    priority: int = 5  # 1 = highest
    meta: dict[str, Any] = field(default_factory=dict)
    locale: str = "ru"

    def key(self) -> str:
        return f"{self.tenant_id or 'default'}:{self.owner_id}:{self.session_id or '-'}"


@dataclass
class ExecutionNode:
    id: str
    name: str
    backend: ExecutorBackend = ExecutorBackend.INTERNAL
    queue: QueueKind = QueueKind.TASK
    payload: dict[str, Any] = field(default_factory=dict)
    depends_on: tuple[str, ...] = ()
    gpu_required: bool = False
    timeout_sec: float = 120.0


@dataclass
class ExecutionGraph:
    nodes: list[ExecutionNode] = field(default_factory=list)

    def add(self, node: ExecutionNode) -> None:
        self.nodes.append(node)

    def topological_order(self) -> list[ExecutionNode]:
        by_id = {n.id: n for n in self.nodes}
        seen: set[str] = set()
        order: list[ExecutionNode] = []

        def visit(nid: str) -> None:
            if nid in seen:
                return
            seen.add(nid)
            node = by_id.get(nid)
            if not node:
                return
            for dep in node.depends_on:
                visit(dep)
            order.append(node)

        for n in self.nodes:
            visit(n.id)
        return order


@dataclass
class ExecutionPlan:
    id: str
    context: ExecutionContext
    graph: ExecutionGraph
    created_at: float = field(default_factory=time.time)
    label: str = ""

    @classmethod
    def from_single(
        cls,
        context: ExecutionContext,
        *,
        name: str,
        backend: ExecutorBackend = ExecutorBackend.PIPELINE,
        queue: QueueKind = QueueKind.AI,
        payload: dict[str, Any] | None = None,
        gpu_required: bool = False,
    ) -> ExecutionPlan:
        node = ExecutionNode(
            id="n1",
            name=name,
            backend=backend,
            queue=queue,
            payload=payload or {},
            gpu_required=gpu_required,
        )
        return cls(
            id=str(uuid.uuid4()),
            context=context,
            graph=ExecutionGraph(nodes=[node]),
            label=name,
        )


@dataclass
class ExecutionState:
    plan_id: str
    lifecycle: TaskLifecycle = TaskLifecycle.CREATED
    progress: float = 0.0
    result: dict[str, Any] | None = None
    error: str | None = None
    worker_id: str | None = None
    queue: QueueKind | None = None
    started_at: float | None = None
    finished_at: float | None = None
    cost: float = 0.0
    retries: int = 0
    node_results: dict[str, Any] = field(default_factory=dict)

    def duration_sec(self) -> float | None:
        if self.started_at is None:
            return None
        end = self.finished_at or time.time()
        return round(end - self.started_at, 3)


@dataclass
class HerculesJob:
    id: str
    plan: ExecutionPlan
    state: ExecutionState
    external_job_id: str | None = None  # platform_jobs / pipeline id

    def status_line_ru(self) -> str:
        return (
            f"#{self.id[:8]} · {self.state.lifecycle.value} · "
            f"{self.plan.label or 'задача'} · "
            f"{self.state.progress:.0%}"
        )
