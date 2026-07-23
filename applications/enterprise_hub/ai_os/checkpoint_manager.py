"""Checkpoint manager — snapshots for resume after failure."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.ai_os.task_queue import TaskQueue
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class CheckpointManager:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.tasks = TaskQueue(self.store)

    def save(self, *, task_id: str, snapshot: dict[str, Any] | None = None) -> dict[str, Any]:
        task = self.tasks.get(task_id)
        cid = _id("aios_cp")
        return self.store.aios_checkpoints.save(
            cid,
            {
                "checkpoint_id": cid,
                "task_id": task_id,
                "state": task.get("state"),
                "snapshot": snapshot or {"task": dict(task)},
                "at": _now(),
            },
        )

    def latest(self, *, task_id: str) -> dict[str, Any] | None:
        items = [c for c in self.store.aios_checkpoints.list_all() if c.get("task_id") == task_id]
        if not items:
            return None
        return sorted(items, key=lambda c: c.get("at", ""), reverse=True)[0]
