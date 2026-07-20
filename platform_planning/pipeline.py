# Planning pipeline — goal to executable workflow.

from __future__ import annotations

import time
import uuid

from platform_planning.models import (
    ExecutionPlan,
    PlanCandidate,
    PlanningContext,
    PlanningResult,
    PlanningStrategy,
)
from platform_planning.strategies.builtin import STRATEGY_REGISTRY
from platform_planning.validator import PlanValidator, plan_validator


class PlanningPipeline:
    def __init__(self, validator: PlanValidator | None = None) -> None:
        self._validator = validator or plan_validator

    async def run(
        self,
        context: PlanningContext,
        strategy: PlanningStrategy | str = PlanningStrategy.DEPENDENCY_AWARE,
    ) -> PlanningResult:
        started = time.monotonic()
        strategy_key = strategy.value if isinstance(strategy, PlanningStrategy) else strategy

        if strategy_key not in STRATEGY_REGISTRY:
            strategy_key = "dependency_aware"

        # Analyze resources (already in context)
        agents = context.available_agents or ([context.agent_id] if context.agent_id else [])
        tools = context.available_tools
        cost_per_step = 1.0

        # Generate candidates
        impl = STRATEGY_REGISTRY[strategy_key]
        candidate = impl.generate(context)
        candidates = [candidate]

        # Build execution plan
        plan = ExecutionPlan(
            plan_id=str(uuid.uuid4()),
            goal=context.goal,
            strategy=PlanningStrategy(strategy_key),
            steps=list(candidate.steps),
            estimated_cost=candidate.estimated_cost,
            status="validated",
            metadata={
                "agents": agents,
                "tools": tools,
                "intent": context.intent or context.reasoning_result.get("intent"),
            },
        )

        # Validate
        validation_errors: list[str] = []
        try:
            self._validator.validate(plan, context)
            validation_passed = True
        except Exception as exc:
            validation_passed = False
            validation_errors = getattr(exc, "details", [str(exc)])

        # Produce workflow definition
        workflow_def = self._to_workflow(plan, context)

        return PlanningResult(
            plan=plan,
            candidates=candidates,
            validation_passed=validation_passed,
            validation_errors=validation_errors,
            workflow_definition=workflow_def,
            planning_time_ms=round((time.monotonic() - started) * 1000, 2),
            success=validation_passed,
            error="; ".join(validation_errors) if validation_errors else None,
        )

    def _to_workflow(self, plan: ExecutionPlan, context: PlanningContext) -> dict:
        from platform_workflow.models import TaskType, WorkflowStep

        steps = []
        for ps in plan.steps:
            steps.append(
                WorkflowStep(
                    step_id=ps.step_id,
                    name=ps.name,
                    capability=ps.capability,
                    task_type=TaskType.AGENT if ps.capability else TaskType.SYSTEM,
                    depends_on=list(ps.depends_on),
                    metadata={"tool_id": ps.tool_id, "agent_id": ps.agent_id or context.agent_id},
                )
            )
        return {
            "name": f"Plan: {plan.goal[:60]}",
            "plan_id": plan.plan_id,
            "steps": [{"step_id": s.step_id, "name": s.name, "capability": s.capability, "depends_on": s.depends_on} for s in plan.steps],
            "workflow_steps": steps,
            "estimated_cost": plan.estimated_cost,
        }


planning_pipeline = PlanningPipeline()
