"""Central AI Orchestrator — distribute, select, control, aggregate, reassign."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.ai_orchestrator.agents.registry import AgentRegistry
from applications.enterprise_hub.ai_orchestrator.context_manager import ContextManager
from applications.enterprise_hub.ai_orchestrator.dispatcher import Dispatcher
from applications.enterprise_hub.ai_orchestrator.execution_engine import ExecutionEngine
from applications.enterprise_hub.ai_orchestrator.memory_router import MemoryRouter
from applications.enterprise_hub.ai_orchestrator.planner import Planner
from applications.enterprise_hub.ai_orchestrator.policy_engine import PolicyEngine
from applications.enterprise_hub.ai_orchestrator.result_aggregator import ResultAggregator
from applications.enterprise_hub.ai_orchestrator.scheduler import Scheduler
from applications.enterprise_hub.ai_orchestrator.task_manager import TaskManager
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class AIOrchestrator:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.tasks = TaskManager(self.store)
        self.planner = Planner(self.store)
        self.dispatcher = Dispatcher(self.store)
        self.scheduler = Scheduler(self.store)
        self.execution = ExecutionEngine(self.store)
        self.context = ContextManager(self.store)
        self.memory = MemoryRouter(self.store)
        self.aggregator = ResultAggregator(self.store)
        self.policy = PolicyEngine(self.store)
        self.registry = AgentRegistry(self.store)

    def orchestrate(
        self,
        *,
        request: str,
        strategy: str = "sequential",
        priority: str = "normal",
    ) -> dict[str, Any]:
        policy = self.policy.evaluate(strategy=strategy, estimated_cost=0.5)
        if not policy.get("allowed", True):
            raise ValidationError(f"policy blocked orchestration: {policy.get('notes')}")

        task = self.tasks.create(request=request, priority=priority)
        schedule = self.scheduler.enqueue(task_id=task["task_id"])
        plan = self.planner.plan(task_id=task["task_id"])
        ctx = self.context.open(task_id=task["task_id"], seed={"request": request})
        self.memory.route(task_id=task["task_id"], tier="short_term", key="request", value=request)
        self.memory.route(task_id=task["task_id"], tier="corporate", key="playbook", value="proposal")

        dispatch = self.dispatcher.dispatch(
            task_id=task["task_id"], plan_id=plan["plan_id"], strategy=strategy
        )
        execution = self.execution.run(task_id=task["task_id"], dispatch_id=dispatch["dispatch_id"])

        for step in execution.get("step_results") or []:
            if step.get("agent_id") and step.get("status") == "ok":
                self.context.append(
                    context_id=ctx["context_id"],
                    agent_id=step["agent_id"],
                    payload={"summary": step.get("summary"), "specialization": step.get("specialization")},
                )

        # Reassign failed steps via backup on a second pass when needed
        failed = [s for s in execution.get("step_results") or [] if s.get("status") != "ok"]
        reassigned = []
        if failed:
            re_dispatch = self.dispatcher.dispatch(
                task_id=task["task_id"], plan_id=plan["plan_id"], strategy=strategy
            )
            re_exec = self.execution.run(
                task_id=task["task_id"], dispatch_id=re_dispatch["dispatch_id"], max_retries=1
            )
            execution = re_exec
            reassigned.append(re_dispatch["dispatch_id"])

        aggregation = self.aggregator.aggregate(execution_id=execution["execution_id"])
        return {
            "task_id": task["task_id"],
            "schedule_id": schedule["schedule_id"],
            "plan_id": plan["plan_id"],
            "context_id": ctx["context_id"],
            "dispatch_id": dispatch["dispatch_id"],
            "execution_id": execution["execution_id"],
            "aggregation_id": aggregation["aggregation_id"],
            "policy_eval_id": policy["eval_id"],
            "reassigned_dispatch_ids": reassigned,
            "result": aggregation.get("result"),
        }
