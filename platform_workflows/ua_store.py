"""Epic 45.3 — Universal Automation in-memory store (cross-channel)."""
from __future__ import annotations
import threading, time, uuid
from dataclasses import dataclass, field
from typing import Any

def _now() -> float: return time.time()
def new_id(p: str = "wf") -> str: return f"{p}_{uuid.uuid4().hex[:12]}"

@dataclass
class WorkflowSpec:
    id: str
    owner_id: str
    title: str
    blocks: list[dict[str, Any]]
    vertical: str = "company"
    template_id: str | None = None
    json_def: dict[str, Any] = field(default_factory=dict)
    channel: str = "web"
    created_at: float = field(default_factory=_now)
    updated_at: float = field(default_factory=_now)
    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "owner_id": self.owner_id, "title": self.title, "blocks": self.blocks,
                "vertical": self.vertical, "template_id": self.template_id, "json": self.json_def,
                "channel": self.channel, "created_at": self.created_at, "updated_at": self.updated_at}

@dataclass
class WorkflowRun:
    id: str
    workflow_id: str
    owner_id: str
    status: str = "pending"  # pending|running|awaiting_approval|completed|failed|cancelled
    steps: list[dict[str, Any]] = field(default_factory=list)
    current_step: int = 0
    cost: float = 0.0
    models: list[str] = field(default_factory=list)
    logs: list[str] = field(default_factory=list)
    result: dict[str, Any] = field(default_factory=dict)
    channel: str = "web"
    via_hercules: bool = True
    created_at: float = field(default_factory=_now)
    updated_at: float = field(default_factory=_now)
    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "workflow_id": self.workflow_id, "owner_id": self.owner_id, "status": self.status,
                "steps": self.steps, "current_step": self.current_step, "step_label": f"Шаг {self.current_step+1} из {max(len(self.steps),1)}",
                "cost": self.cost, "models": list(self.models), "logs": list(self.logs), "result": self.result,
                "channel": self.channel, "via_hercules": self.via_hercules, "created_at": self.created_at, "updated_at": self.updated_at}

@dataclass
class ScheduledJob:
    id: str
    owner_id: str
    workflow_id: str
    schedule: str  # once|daily|weekly|monthly|event|after|night
    next_run_at: float
    enabled: bool = True
    meta: dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "owner_id": self.owner_id, "workflow_id": self.workflow_id, "schedule": self.schedule,
                "next_run_at": self.next_run_at, "enabled": self.enabled, "meta": self.meta}

class UAStore:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.workflows: dict[str, WorkflowSpec] = {}
        self.runs: dict[str, WorkflowRun] = {}
        self.jobs: dict[str, ScheduledJob] = {}
        self.history: list[dict[str, Any]] = []
    def clear(self) -> None:
        with self._lock:
            self.workflows.clear(); self.runs.clear(); self.jobs.clear(); self.history.clear()

ua_store = UAStore()
