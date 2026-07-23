"""Supervisor — progress, errors, timeouts, budget, hung processes."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.ai_os.state_manager import StateManager
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class Supervisor:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.states = StateManager(self.store)

    def inspect(self, *, task_id: str, budget: float = 10.0, spent: float = 0.0, timeout: bool = False) -> dict[str, Any]:
        task = self.states.tasks.get(task_id)
        issues = []
        if timeout:
            issues.append("timeout")
        if spent > budget:
            issues.append("budget_exceeded")
        if task.get("state") == "running" and not task.get("heartbeat_at"):
            issues.append("possible_hang")
        healthy = not issues
        if "budget_exceeded" in issues:
            self.states.transition(task_id=task_id, state="blocked", note="budget")
        elif timeout:
            self.states.transition(task_id=task_id, state="failed", note="timeout")
        sid = _id("aios_sup")
        return self.store.aios_supervisions.save(
            sid,
            {
                "supervision_id": sid,
                "task_id": task_id,
                "healthy": healthy,
                "issues": issues,
                "state": task.get("state"),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "supervisions": self.store.aios_supervisions.count(),
            "running": len(self.states.by_state("running")),
            "failed": len(self.states.by_state("failed")),
            "blocked": len(self.states.by_state("blocked")),
        }
