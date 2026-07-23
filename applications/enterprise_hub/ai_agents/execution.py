"""Agent execution — tasks, queue, prioritization, parallel/sequential, retry, history."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AgentExecution:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def assign_task(
        self,
        *,
        agent_id: str,
        title: str,
        priority: int = 5,
        mode: str = "sequential",
    ) -> dict[str, Any]:
        if self.store.aa_agents.get(agent_id) is None:
            raise NotFoundError(f"agent not found: {agent_id}")
        if not title:
            raise ValidationError("title required")
        mode_n = mode.lower().strip()
        if mode_n not in ("sequential", "parallel"):
            raise ValidationError("mode must be sequential or parallel")
        tid = _id("aa_task")
        task = self.store.aa_tasks.save(
            tid,
            {
                "task_id": tid,
                "agent_id": agent_id,
                "title": title,
                "priority": int(priority),
                "mode": mode_n,
                "status": "queued",
                "at": _now(),
            },
        )
        qid = _id("aa_queue")
        self.store.aa_queue.save(
            qid,
            {
                "queue_id": qid,
                "task_id": tid,
                "priority": int(priority),
                "at": _now(),
            },
        )
        return task

    def prioritize(self, *, task_id: str, priority: int) -> dict[str, Any]:
        task = self.store.aa_tasks.get(task_id)
        if task is None:
            raise NotFoundError(f"task not found: {task_id}")
        task["priority"] = int(priority)
        task["at"] = _now()
        return self.store.aa_tasks.save(task_id, task)

    def execute(self, *, task_id: str) -> dict[str, Any]:
        task = self.store.aa_tasks.get(task_id)
        if task is None:
            raise NotFoundError(f"task not found: {task_id}")
        task["status"] = "completed"
        task["at"] = _now()
        self.store.aa_tasks.save(task_id, task)
        eid = _id("aa_exec")
        return self.store.aa_executions.save(
            eid,
            {
                "execution_id": eid,
                "task_id": task_id,
                "agent_id": task["agent_id"],
                "mode": task.get("mode", "sequential"),
                "status": "completed",
                "at": _now(),
            },
        )

    def retry(self, *, task_id: str, reason: str = "") -> dict[str, Any]:
        task = self.store.aa_tasks.get(task_id)
        if task is None:
            raise NotFoundError(f"task not found: {task_id}")
        task["status"] = "retrying"
        task["at"] = _now()
        self.store.aa_tasks.save(task_id, task)
        rid = _id("aa_retry")
        return self.store.aa_retries.save(
            rid,
            {
                "retry_id": rid,
                "task_id": task_id,
                "reason": reason,
                "at": _now(),
            },
        )

    def record_history(self, *, task_id: str, detail: str = "") -> dict[str, Any]:
        if self.store.aa_tasks.get(task_id) is None:
            raise NotFoundError(f"task not found: {task_id}")
        hid = _id("aa_hist")
        return self.store.aa_history.save(
            hid,
            {
                "history_id": hid,
                "task_id": task_id,
                "detail": detail,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "tasks": self.store.aa_tasks.count(),
            "queue": self.store.aa_queue.count(),
            "executions": self.store.aa_executions.count(),
            "retries": self.store.aa_retries.count(),
            "history": self.store.aa_history.count(),
        }
