"""Epic 45.3 — workflow domain events (local + optional bus)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable
import time

@dataclass
class WorkflowEvent:
    type: str
    owner_id: str
    workflow_id: str = ""
    run_id: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    ts: float = field(default_factory=time.time)

class WorkflowEventBus:
    def __init__(self) -> None:
        self._handlers: list[Callable[[WorkflowEvent], None]] = []
        self._history: list[WorkflowEvent] = []
    def subscribe(self, fn: Callable[[WorkflowEvent], None]) -> None:
        self._handlers.append(fn)
    def emit(self, event: WorkflowEvent) -> None:
        self._history.append(event)
        for h in list(self._handlers):
            try: h(event)
            except Exception: pass
    def recent(self, limit: int = 50) -> list[dict[str, Any]]:
        return [{"type": e.type, "owner_id": e.owner_id, "workflow_id": e.workflow_id, "run_id": e.run_id, "payload": e.payload, "ts": e.ts} for e in self._history[-limit:]]

workflow_events = WorkflowEventBus()
