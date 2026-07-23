"""Dispatcher — select agents, sequence, backup, parallel eligibility."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.ai_orchestrator.agents.registry import AgentRegistry
from applications.enterprise_hub.ai_orchestrator.models import STRATEGIES
from applications.enterprise_hub.ai_orchestrator.task_manager import TaskManager
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class Dispatcher:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.registry = AgentRegistry(self.store)
        self.tasks = TaskManager(self.store)

    def dispatch(
        self,
        *,
        task_id: str,
        plan_id: str,
        strategy: str = "sequential",
    ) -> dict[str, Any]:
        self.tasks.get(task_id)
        plan = self.store.aop_plans.get(plan_id)
        if not plan:
            raise ValidationError(f"plan not found: {plan_id}")
        st = strategy.lower().strip()
        if st not in STRATEGIES:
            raise ValidationError(f"strategy must be one of {list(STRATEGIES)}")

        assignments = []
        for step in plan.get("steps") or []:
            spec = step.get("specialization", "")
            candidates = self.registry.list_ready(specialization=spec)
            primary = candidates[0] if candidates else None
            backup = candidates[1] if len(candidates) > 1 else None
            assignments.append(
                {
                    "specialization": spec,
                    "description": step.get("description"),
                    "agent_id": primary["agent_id"] if primary else None,
                    "backup_agent_id": backup["agent_id"] if backup else None,
                    "parallel_ok": st in ("parallel", "voting", "collaborative"),
                }
            )

        did = _id("aop_disp")
        result = self.store.aop_dispatches.save(
            did,
            {
                "dispatch_id": did,
                "task_id": task_id,
                "plan_id": plan_id,
                "strategy": st,
                "assignments": assignments,
                "at": _now(),
            },
        )
        self.tasks.set_status(task_id=task_id, status="dispatched", dispatch_id=did)
        return result
