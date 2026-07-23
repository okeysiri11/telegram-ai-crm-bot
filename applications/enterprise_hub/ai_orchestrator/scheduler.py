"""Scheduler — priority queues and run windows."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.ai_orchestrator.task_manager import TaskManager
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


PRIORITY_RANK = {"critical": 0, "high": 1, "normal": 2, "low": 3}


class Scheduler:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.tasks = TaskManager(self.store)

    def enqueue(self, *, task_id: str) -> dict[str, Any]:
        task = self.tasks.get(task_id)
        sid = _id("aop_sch")
        return self.store.aop_schedule.save(
            sid,
            {
                "schedule_id": sid,
                "task_id": task_id,
                "priority": task.get("priority", "normal"),
                "rank": PRIORITY_RANK.get(task.get("priority", "normal"), 2),
                "queued_at": _now(),
            },
        )

    def next_batch(self, *, limit: int = 5) -> list[dict[str, Any]]:
        items = sorted(
            self.store.aop_schedule.list_all(),
            key=lambda x: (x.get("rank", 2), x.get("queued_at", "")),
        )
        return items[: max(1, limit)]

    def status(self) -> dict[str, Any]:
        return {"queued": self.store.aop_schedule.count()}
