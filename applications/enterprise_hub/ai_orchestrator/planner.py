"""Task planner — decompose complex requests into agent steps."""

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


DEFAULT_PIPELINE = (
    ("legal", "legal review"),
    ("finance", "financial analysis"),
    ("crm", "crm enrichment"),
    ("writer", "draft composition"),
    ("aggregator", "final aggregation"),
)


class Planner:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.tasks = TaskManager(self.store)

    def plan(self, *, task_id: str, steps: list[dict[str, str]] | None = None) -> dict[str, Any]:
        task = self.tasks.get(task_id)
        planned_steps = steps or [
            {"specialization": spec, "description": desc} for spec, desc in DEFAULT_PIPELINE
        ]
        pid = _id("aop_plan")
        plan = self.store.aop_plans.save(
            pid,
            {
                "plan_id": pid,
                "task_id": task_id,
                "request": task["request"],
                "steps": planned_steps,
                "created_at": _now(),
            },
        )
        self.tasks.set_status(task_id=task_id, status="planned", plan_id=pid)
        return plan
