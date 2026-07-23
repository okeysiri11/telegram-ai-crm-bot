"""Autonomous AIOS Suite facade — Sprint 20.4."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.ai_os.ai_os import AutonomousAIOS
from applications.enterprise_hub.ai_os.analytics.efficiency import EfficiencyAnalytics
from applications.enterprise_hub.ai_os.analytics.optimization import OptimizationAnalytics
from applications.enterprise_hub.ai_os.analytics.productivity import ProductivityAnalytics
from applications.enterprise_hub.ai_os.checkpoint_manager import CheckpointManager
from applications.enterprise_hub.ai_os.executor import Executor
from applications.enterprise_hub.ai_os.execution.collaborative import CollaborativeExecution
from applications.enterprise_hub.ai_os.execution.distributed import DistributedExecution
from applications.enterprise_hub.ai_os.execution.parallel import ParallelExecution
from applications.enterprise_hub.ai_os.execution.recursive import RecursiveExecution
from applications.enterprise_hub.ai_os.execution.sequential import SequentialExecution
from applications.enterprise_hub.ai_os.goal_manager import GoalManager
from applications.enterprise_hub.ai_os.governance.approvals import ApprovalGate
from applications.enterprise_hub.ai_os.governance.escalation import EscalationEngine
from applications.enterprise_hub.ai_os.governance.limits import LimitsPolicy
from applications.enterprise_hub.ai_os.governance.safety import SafetyPolicy
from applications.enterprise_hub.ai_os.objective_manager import ObjectiveManager
from applications.enterprise_hub.ai_os.planner import Planner
from applications.enterprise_hub.ai_os.recovery import RecoveryEngine
from applications.enterprise_hub.ai_os.scheduler import Scheduler
from applications.enterprise_hub.ai_os.state_manager import StateManager
from applications.enterprise_hub.ai_os.supervisor import Supervisor
from applications.enterprise_hub.ai_os.task_queue import TaskQueue
from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class AutonomousAIOSSuite:
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
        self.aios = AutonomousAIOS(self.store)
        self.approvals = ApprovalGate(self.store)
        self.limits = LimitsPolicy(self.store)
        self.safety = SafetyPolicy(self.store)
        self.escalation = EscalationEngine(self.store)
        self.productivity = ProductivityAnalytics(self.store)
        self.efficiency = EfficiencyAnalytics(self.store)
        self.optimization = OptimizationAnalytics(self.store)
        self.modes = {
            "sequential": SequentialExecution(),
            "parallel": ParallelExecution(),
            "distributed": DistributedExecution(),
            "recursive": RecursiveExecution(),
            "collaborative": CollaborativeExecution(),
        }

    def dashboard(self) -> dict[str, Any]:
        states = self.states.status()["states"]
        prod = self.productivity.report()
        eff = self.efficiency.report()
        opt = self.optimization.report()
        return {
            "active_tasks": states.get("running", 0),
            "completed_tasks": states.get("completed", 0),
            "failed_tasks": states.get("failed", 0),
            "blocked_tasks": states.get("blocked", 0),
            "hung_candidates": states.get("suspended", 0),
            "productivity_id": prod["analytics_id"],
            "efficiency_id": eff["analytics_id"],
            "optimization_id": opt["analytics_id"],
            "success_rate": prod.get("success_rate"),
            "total_cost": prod.get("total_cost"),
            "bottlenecks": eff.get("bottlenecks"),
            "recommendations": opt.get("recommendations"),
        }

    def bootstrap(self) -> dict[str, Any]:
        limits = self.limits.define(max_budget=25.0, max_minutes=120)
        safety = self.safety.evaluate(operation="crm.update")
        blocked = self.safety.evaluate(operation="delete_production")

        run_seq = self.aios.run_goal(
            title="Подготовить коммерческое предложение",
            kind="operational",
            priority="high",
            mode="sequential",
            budget=5.0,
            confirmed=True,
        )
        run_par = self.aios.run_goal(
            title="Параллельный сбор рыночных данных",
            kind="operational",
            priority="normal",
            mode="parallel",
            budget=3.0,
            confirmed=True,
        )
        run_col = self.aios.run_goal(
            title="Совместная проверка контракта",
            kind="strategic",
            priority="critical",
            mode="collaborative",
            budget=8.0,
            confirmed=True,
        )

        # simulate failure + recovery on a queued standalone task
        fail_task = self.queue.enqueue(title="fragile step", priority="low")
        self.states.transition(task_id=fail_task["task_id"], state="running", note="start")
        self.checkpoints.save(task_id=fail_task["task_id"], snapshot={"phase": 1})
        self.states.transition(task_id=fail_task["task_id"], state="failed", note="simulated")
        recovery = self.recovery.recover(task_id=fail_task["task_id"], action="retry")
        esc = self.escalation.escalate(task_id=fail_task["task_id"], reason="repeated failure", level="ops")
        approval = self.approvals.require(goal_id=run_col["goal_id"], reason="critical goal")
        approved = self.approvals.approve(approval_id=approval["approval_id"], actor="cfo")

        dash = self.dashboard()

        return {
            "bootstrap": True,
            "limit_id": limits["limit_id"],
            "safety_ok_id": safety["safety_id"],
            "safety_blocked_id": blocked["safety_id"],
            "safety_blocked_allowed": blocked["allowed"],
            "run_sequential": run_seq,
            "run_parallel": run_par,
            "run_collaborative": run_col,
            "recovery_id": recovery["recovery_id"],
            "escalation_id": esc["escalation_id"],
            "approval_id": approved["approval_id"],
            "dashboard": dash,
            "modes": {k: v.describe() for k, v in self.modes.items()},
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "goals": self.goals.status(),
            "objectives": self.objectives.status(),
            "queue": self.queue.status(),
            "scheduler": self.scheduler.status(),
            "executor": self.executor.status(),
            "supervisor": self.supervisor.status(),
            "states": self.states.status(),
        }


aios = AutonomousAIOSSuite()
