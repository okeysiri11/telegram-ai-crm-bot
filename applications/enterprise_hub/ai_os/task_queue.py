"""Task queue — priority queue for AIOS work items."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.ai_os.models import PRIORITIES
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


PRIORITY_RANK = {"critical": 0, "high": 1, "normal": 2, "low": 3}


class TaskQueue:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def enqueue(
        self,
        *,
        title: str,
        goal_id: str | None = None,
        objective_id: str | None = None,
        priority: str = "normal",
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not title:
            raise ValidationError("title is required")
        pr = priority.lower().strip()
        if pr not in PRIORITIES:
            raise ValidationError(f"priority must be one of {list(PRIORITIES)}")
        tid = _id("aios_task")
        return self.store.aios_tasks.save(
            tid,
            {
                "task_id": tid,
                "title": title.strip(),
                "goal_id": goal_id,
                "objective_id": objective_id,
                "priority": pr,
                "rank": PRIORITY_RANK[pr],
                "payload": payload or {},
                "state": "planned",
                "queued_at": _now(),
            },
        )

    def get(self, task_id: str) -> dict[str, Any]:
        item = self.store.aios_tasks.get(task_id)
        if not item:
            raise NotFoundError(f"task not found: {task_id}")
        return item

    def next_batch(self, *, limit: int = 5) -> list[dict[str, Any]]:
        items = [
            t
            for t in self.store.aios_tasks.list_all()
            if t.get("state") in ("planned", "waiting")
        ]
        items.sort(key=lambda t: (t.get("rank", 2), t.get("queued_at", "")))
        return items[: max(1, limit)]

    def status(self) -> dict[str, Any]:
        return {"tasks": self.store.aios_tasks.count(), "queued": len(self.next_batch(limit=1000))}
