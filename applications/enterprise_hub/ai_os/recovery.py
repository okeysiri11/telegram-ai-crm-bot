"""Recovery engine — retry, reassign, rollback, resume."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.ai_os.checkpoint_manager import CheckpointManager
from applications.enterprise_hub.ai_os.state_manager import StateManager
from applications.enterprise_hub.ai_os.task_queue import TaskQueue
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class RecoveryEngine:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.tasks = TaskQueue(self.store)
        self.states = StateManager(self.store)
        self.checkpoints = CheckpointManager(self.store)

    def recover(
        self,
        *,
        task_id: str,
        action: str = "retry",
        new_assignee: str | None = None,
    ) -> dict[str, Any]:
        task = self.tasks.get(task_id)
        cp = self.checkpoints.latest(task_id=task_id)
        act = action.lower().strip()
        if act == "reassign" and new_assignee:
            task.setdefault("payload", {})["assignee"] = new_assignee
            self.store.aios_tasks.save(task_id, task)
        if act == "rollback" and cp:
            snap = (cp.get("snapshot") or {}).get("task") or {}
            task["state"] = snap.get("state", "planned")
            self.store.aios_tasks.save(task_id, task)
        else:
            self.states.transition(task_id=task_id, state="planned", note=f"recovery:{act}")
        rid = _id("aios_rcv")
        return self.store.aios_recoveries.save(
            rid,
            {
                "recovery_id": rid,
                "task_id": task_id,
                "action": act,
                "checkpoint_id": (cp or {}).get("checkpoint_id"),
                "at": _now(),
            },
        )
