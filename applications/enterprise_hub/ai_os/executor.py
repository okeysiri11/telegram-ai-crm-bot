"""Execution engine — run tasks in various modes with supervision."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.ai_os.checkpoint_manager import CheckpointManager
from applications.enterprise_hub.ai_os.models import EXECUTION_MODES
from applications.enterprise_hub.ai_os.state_manager import StateManager
from applications.enterprise_hub.ai_os.supervisor import Supervisor
from applications.enterprise_hub.ai_os.task_queue import TaskQueue
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class Executor:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.tasks = TaskQueue(self.store)
        self.states = StateManager(self.store)
        self.checkpoints = CheckpointManager(self.store)
        self.supervisor = Supervisor(self.store)

    def run_plan(
        self,
        *,
        plan_id: str,
        budget: float = 10.0,
        confirmed: bool = True,
    ) -> dict[str, Any]:
        plan = self.store.aios_plans.get(plan_id)
        if not plan:
            raise NotFoundError(f"plan not found: {plan_id}")
        mode = plan.get("mode", "sequential")
        if mode not in EXECUTION_MODES:
            raise ValidationError(f"invalid mode: {mode}")

        # governance check stored separately; executor respects confirmation flag
        if not confirmed:
            raise ValidationError("user confirmation required")

        results = []
        spent = 0.0
        for tid in plan.get("task_ids") or []:
            self.states.transition(task_id=tid, state="running", note=f"mode:{mode}")
            task = self.tasks.get(tid)
            task["heartbeat_at"] = _now()
            self.store.aios_tasks.save(tid, task)
            cost = 0.05
            spent += cost
            step_result = {
                "task_id": tid,
                "assignee": (task.get("payload") or {}).get("assignee", "system"),
                "step": (task.get("payload") or {}).get("step"),
                "status": "ok",
                "cost": cost,
                "output": f"completed {task.get('title')}",
            }
            self.checkpoints.save(task_id=tid, snapshot={"result": step_result, "task": dict(task)})
            self.supervisor.inspect(task_id=tid, budget=budget, spent=spent, timeout=False)
            if spent > budget:
                self.states.transition(task_id=tid, state="blocked", note="budget")
                step_result["status"] = "blocked"
                results.append(step_result)
                break
            self.states.transition(task_id=tid, state="completed", note="ok")
            results.append(step_result)
            # parallel/distributed/collaborative treat remaining as concurrent conceptually
            if mode == "recursive" and step_result.get("step") == "plan":
                # nested micro-step already represented in plan
                pass

        eid = _id("aios_exec")
        return self.store.aios_executions.save(
            eid,
            {
                "execution_id": eid,
                "plan_id": plan_id,
                "mode": mode,
                "results": results,
                "spent": spent,
                "budget": budget,
                "status": "completed" if all(r.get("status") == "ok" for r in results) else "partial",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"executions": self.store.aios_executions.count()}
