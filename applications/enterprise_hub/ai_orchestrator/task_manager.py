"""Task manager — create, track, cancel AI orchestration tasks."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.ai_orchestrator.models import TASK_PRIORITIES, TASK_STATUSES
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class TaskManager:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def create(
        self,
        *,
        request: str,
        priority: str = "normal",
        meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not request or not str(request).strip():
            raise ValidationError("request is required")
        pr = priority.lower().strip()
        if pr not in TASK_PRIORITIES:
            raise ValidationError(f"priority must be one of {list(TASK_PRIORITIES)}")
        tid = _id("aop_task")
        return self.store.aop_tasks.save(
            tid,
            {
                "task_id": tid,
                "request": request.strip(),
                "priority": pr,
                "status": "pending",
                "meta": meta or {},
                "created_at": _now(),
            },
        )

    def get(self, task_id: str) -> dict[str, Any]:
        item = self.store.aop_tasks.get(task_id)
        if not item:
            raise NotFoundError(f"task not found: {task_id}")
        return item

    def set_status(self, *, task_id: str, status: str, **extra: Any) -> dict[str, Any]:
        task = self.get(task_id)
        st = status.lower().strip()
        if st not in TASK_STATUSES:
            raise ValidationError(f"status must be one of {list(TASK_STATUSES)}")
        task["status"] = st
        task.update(extra)
        task["updated_at"] = _now()
        return self.store.aop_tasks.save(task_id, task)

    def cancel(self, *, task_id: str) -> dict[str, Any]:
        return self.set_status(task_id=task_id, status="canceled")

    def status(self) -> dict[str, Any]:
        return {"tasks": self.store.aop_tasks.count(), "statuses": list(TASK_STATUSES)}
