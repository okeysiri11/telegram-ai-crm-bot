"""Central Autonomous AIOS coordinator."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.ai_os.checkpoint_manager import CheckpointManager
from applications.enterprise_hub.ai_os.executor import Executor
from applications.enterprise_hub.ai_os.goal_manager import GoalManager
from applications.enterprise_hub.ai_os.objective_manager import ObjectiveManager
from applications.enterprise_hub.ai_os.planner import Planner
from applications.enterprise_hub.ai_os.recovery import RecoveryEngine
from applications.enterprise_hub.ai_os.scheduler import Scheduler
from applications.enterprise_hub.ai_os.state_manager import StateManager
from applications.enterprise_hub.ai_os.supervisor import Supervisor
from applications.enterprise_hub.ai_os.task_queue import TaskQueue
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AutonomousAIOS:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.goals = GoalManager(self.store)
        self.objectives = ObjectiveManager(self.store)
        self.queue = TaskQueue(self.store)
        self.planner = Planner(self.store)
        self.scheduler = Scheduler(self.store)
        self.executor = Executor(self.store)
        self.supervisor = Supervisor(self.store)
        self.states = StateManager(self.store)
        self.checkpoints = CheckpointManager(self.store)
        self.recovery = RecoveryEngine(self.store)

    def run_goal(
        self,
        *,
        title: str,
        kind: str = "operational",
        priority: str = "high",
        mode: str = "sequential",
        budget: float = 10.0,
        confirmed: bool = True,
    ) -> dict[str, Any]:
        goal = self.goals.create(title=title, kind=kind, priority=priority)
        objective = self.objectives.create(goal_id=goal["goal_id"], title=f"Deliver: {title}")
        plan = self.planner.plan(goal_id=goal["goal_id"], mode=mode)
        schedule = self.scheduler.schedule(plan_id=plan["plan_id"])
        memory = self._remember(goal=goal, plan=plan, objective=objective)
        execution = self.executor.run_plan(plan_id=plan["plan_id"], budget=budget, confirmed=confirmed)
        return {
            "goal_id": goal["goal_id"],
            "objective_id": objective["objective_id"],
            "plan_id": plan["plan_id"],
            "schedule_id": schedule["schedule_id"],
            "execution_id": execution["execution_id"],
            "memory_id": memory["memory_id"],
            "status": execution.get("status"),
        }

    def _remember(self, *, goal: dict[str, Any], plan: dict[str, Any], objective: dict[str, Any]) -> dict[str, Any]:
        mid = _id("aios_mem")
        return self.store.aios_task_memory.save(
            mid,
            {
                "memory_id": mid,
                "goal": goal,
                "objective": objective,
                "plan": plan,
                "history": [],
                "decisions": [{"action": "planned", "mode": plan.get("mode")}],
                "tools": [],
                "results": [],
                "documents": [],
                "logs": [{"event": "created", "at": _now()}],
                "at": _now(),
            },
        )
