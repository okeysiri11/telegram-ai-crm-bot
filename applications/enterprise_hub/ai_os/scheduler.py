"""Scheduler — schedule planned tasks for execution."""

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


class Scheduler:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.queue = TaskQueue(self.store)

    def schedule(self, *, plan_id: str) -> dict[str, Any]:
        plan = self.store.aios_plans.get(plan_id)
        from applications.enterprise_hub.shared.exceptions import NotFoundError

        if not plan:
            raise NotFoundError(f"plan not found: {plan_id}")
        batch = []
        for tid in plan.get("task_ids") or []:
            task = self.queue.get(tid)
            batch.append({"task_id": tid, "priority": task.get("priority"), "title": task.get("title")})
        sid = _id("aios_sch")
        return self.store.aios_schedules.save(
            sid,
            {
                "schedule_id": sid,
                "plan_id": plan_id,
                "batch": batch,
                "scheduled_at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"schedules": self.store.aios_schedules.count()}
