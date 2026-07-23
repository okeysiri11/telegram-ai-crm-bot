"""Planning engine — decompose goals into execution plans."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.ai_os.goal_manager import GoalManager
from applications.enterprise_hub.ai_os.models import EXECUTION_MODES
from applications.enterprise_hub.ai_os.task_queue import TaskQueue
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


DEFAULT_STEPS = (
    ("analyze", "context agent"),
    ("plan", "planner agent"),
    ("execute", "ops agent"),
    ("verify", "supervisor agent"),
    ("finalize", "reporter agent"),
)


class Planner:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.goals = GoalManager(self.store)
        self.queue = TaskQueue(self.store)

    def plan(
        self,
        *,
        goal_id: str,
        mode: str = "sequential",
        steps: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        goal = self.goals.get(goal_id)
        m = mode.lower().strip()
        if m not in EXECUTION_MODES:
            raise ValidationError(f"mode must be one of {list(EXECUTION_MODES)}")
        planned = steps or [
            {"step": name, "assignee": assignee, "depends_on": [] if i == 0 else [DEFAULT_STEPS[i - 1][0]]}
            for i, (name, assignee) in enumerate(DEFAULT_STEPS)
        ]
        task_ids = []
        for step in planned:
            task = self.queue.enqueue(
                title=f"{goal['title']}: {step['step']}",
                goal_id=goal_id,
                priority=goal.get("priority", "normal"),
                payload={"step": step["step"], "assignee": step.get("assignee"), "depends_on": step.get("depends_on", [])},
            )
            task_ids.append(task["task_id"])
        pid = _id("aios_plan")
        return self.store.aios_plans.save(
            pid,
            {
                "plan_id": pid,
                "goal_id": goal_id,
                "mode": m,
                "steps": planned,
                "task_ids": task_ids,
                "created_at": _now(),
            },
        )
