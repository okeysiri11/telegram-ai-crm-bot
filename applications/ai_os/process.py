"""Process Manager — AI processes, services, queues, lifecycle, health (Sprint 12.4)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.ai_os.shared.exceptions import NotFoundError, ValidationError
from applications.ai_os.shared.store import AIOSStore, ai_os_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ProcessManager:
    def __init__(self, store: AIOSStore | None = None) -> None:
        self.store = store or ai_os_store

    def start_process(
        self,
        *,
        name: str,
        kind: str = "ai_process",
        priority: int = 5,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("process name required")
        if kind not in {"ai_process", "background_service"}:
            raise ValidationError("kind must be ai_process|background_service")
        pid = f"proc_{uuid.uuid4().hex[:12]}"
        proc = {
            "process_id": pid,
            "name": name,
            "kind": kind,
            "priority": priority,
            "status": "running",
            "health": "healthy",
            "metadata": dict(metadata or {}),
            "started_at": _now(),
            "updated_at": _now(),
        }
        self.store.processes.save(pid, proc)
        return proc

    def get(self, process_id: str) -> dict[str, Any]:
        item = self.store.processes.get(process_id)
        if item is None:
            raise NotFoundError("process", process_id)
        return item

    def enqueue(self, *, queue: str = "default", item: dict[str, Any] | None = None, priority: bool = False) -> dict[str, Any]:
        qid = f"q_{uuid.uuid4().hex[:10]}"
        row = {
            "queue_id": qid,
            "queue": queue,
            "priority_queue": priority,
            "item": dict(item or {}),
            "status": "queued",
            "at": _now(),
        }
        self.store.queues.save(qid, row)
        return row

    def dequeue(self, *, queue: str = "default") -> dict[str, Any] | None:
        items = [
            q
            for q in self.store.queues.list_all()
            if q.get("queue") == queue and q.get("status") == "queued"
        ]
        items.sort(key=lambda q: (0 if q.get("priority_queue") else 1, q.get("at", "")))
        if not items:
            return None
        row = items[0]
        row["status"] = "consumed"
        row["consumed_at"] = _now()
        self.store.queues.save(row["queue_id"], row)
        return row

    def lifecycle(self, process_id: str, *, action: str) -> dict[str, Any]:
        proc = self.get(process_id)
        if action == "stop":
            proc["status"] = "stopped"
        elif action == "restart":
            proc["status"] = "running"
            proc["health"] = "healthy"
        elif action == "pause":
            proc["status"] = "paused"
        else:
            raise ValidationError("action must be stop|restart|pause")
        proc["updated_at"] = _now()
        self.store.processes.save(process_id, proc)
        return proc

    def health_monitor(self, process_id: str, *, healthy: bool = True, detail: str = "") -> dict[str, Any]:
        proc = self.get(process_id)
        proc["health"] = "healthy" if healthy else "unhealthy"
        proc["health_detail"] = detail
        proc["updated_at"] = _now()
        self.store.processes.save(process_id, proc)
        return proc

    def list_processes(self) -> list[dict[str, Any]]:
        return self.store.processes.list_all()

    def status(self) -> dict[str, Any]:
        return {
            "process_manager": "1.0",
            "processes": len(self.list_processes()),
            "queue_depth": len([q for q in self.store.queues.list_all() if q.get("status") == "queued"]),
            "ready": True,
        }


process_manager = ProcessManager()
