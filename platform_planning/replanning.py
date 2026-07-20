# Adaptive replanning — recover from failed steps.

from __future__ import annotations

import logging
import uuid

from platform_planning.models import ExecutionPlan, PlanStep, PlanStepStatus, PlanningContext, PlanningStrategy
from platform_planning.pipeline import PlanningPipeline
from platform_planning.validator import plan_validator

logger = logging.getLogger(__name__)


class ReplanningEngine:
    """Detect failures, generate alternative paths, reuse completed steps."""

    def __init__(self, pipeline: PlanningPipeline | None = None) -> None:
        self._pipeline = pipeline or PlanningPipeline()

    async def replan(
        self,
        plan: ExecutionPlan,
        failed_step_id: str,
        context: PlanningContext,
        *,
        error: str = "",
    ) -> ExecutionPlan:
        logger.info("replanning plan=%s failed_step=%s", plan.plan_id, failed_step_id)
        plan.failed_step_id = failed_step_id
        plan.status = "replanning"

        completed = [s for s in plan.steps if s.status == PlanStepStatus.COMPLETED or s.step_id in plan.completed_steps]
        remaining_context = PlanningContext(
            goal=f"Recover: {context.goal} (after failure at {failed_step_id}: {error})",
            agent_id=context.agent_id,
            user_id=context.user_id,
            intent=context.intent,
            capabilities=context.capabilities,
            available_tools=context.available_tools,
            available_agents=context.available_agents,
            constraints=context.constraints,
            permissions=context.permissions,
        )

        result = await self._pipeline.run(remaining_context, strategy=PlanningStrategy.ADAPTIVE_REPLANNING)
        new_plan = result.plan
        new_plan.plan_id = plan.plan_id
        new_plan.completed_steps = list(plan.completed_steps)
        new_plan.metadata["replan_count"] = plan.metadata.get("replan_count", 0) + 1
        new_plan.metadata["reused_steps"] = [s.step_id for s in completed]

        # Prepend completed steps
        reused = [PlanStep(
            step_id=s.step_id, name=s.name, capability=s.capability,
            agent_id=s.agent_id, tool_id=s.tool_id, status=PlanStepStatus.COMPLETED,
            output=dict(s.output),
        ) for s in completed]

        # Wire dependencies from last reused to first new
        if reused and new_plan.steps:
            new_plan.steps[0].depends_on = [reused[-1].step_id]

        new_plan.steps = reused + new_plan.steps
        new_plan.estimated_cost = sum(s.estimated_cost for s in new_plan.steps)
        new_plan.status = "replanned"

        try:
            plan_validator.validate(new_plan, context)
        except Exception:
            new_plan.status = "replanned_with_warnings"

        return new_plan

    def mark_step_completed(self, plan: ExecutionPlan, step_id: str, output: dict | None = None) -> None:
        for step in plan.steps:
            if step.step_id == step_id:
                step.status = PlanStepStatus.COMPLETED
                step.output = output or {}
                if step_id not in plan.completed_steps:
                    plan.completed_steps.append(step_id)
                return

    def mark_step_failed(self, plan: ExecutionPlan, step_id: str) -> None:
        for step in plan.steps:
            if step.step_id == step_id:
                step.status = PlanStepStatus.FAILED
                plan.failed_step_id = step_id
                return


replanning_engine = ReplanningEngine()
