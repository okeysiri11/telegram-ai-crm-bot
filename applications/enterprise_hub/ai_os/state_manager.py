"""State manager — task lifecycle states."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.ai_os.models import TASK_STATES
from applications.enterprise_hub.ai_os.task_queue import TaskQueue
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class StateManager:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.tasks = TaskQueue(self.store)

    def transition(self, *, task_id: str, state: str, note: str = "") -> dict[str, Any]:
        task = self.tasks.get(task_id)
        st = state.lower().strip()
        if st not in TASK_STATES:
            raise ValidationError(f"state must be one of {list(TASK_STATES)}")
        task["state"] = st
        task["state_updated_at"] = _now()
        if note:
            task.setdefault("state_log", []).append({"state": st, "note": note, "at": _now()})
        return self.store.aios_tasks.save(task_id, task)

    def by_state(self, state: str) -> list[dict[str, Any]]:
        return [t for t in self.store.aios_tasks.list_all() if t.get("state") == state]

    def status(self) -> dict[str, Any]:
        counts = {s: 0 for s in TASK_STATES}
        for t in self.store.aios_tasks.list_all():
            st = t.get("state")
            if st in counts:
                counts[st] += 1
        return {"states": counts}
