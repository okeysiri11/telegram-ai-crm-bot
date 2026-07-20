# PlanningEngine — transform goals into executable multi-step plans.

from __future__ import annotations

import logging

from events.publisher import publish
from platform_planning.config import DEFAULT_PLANNING_CONFIG, PlanningEngineConfig
from platform_planning.exceptions import PlanNotFoundError, PlanningError
from platform_planning.integrations import PlanningIntegrations, planning_integrations
from platform_planning.metrics import PlanningMetrics, planning_metrics
from platform_planning.models import ExecutionPlan, PlanningContext, PlanningResult, PlanningStrategy
from platform_planning.pipeline import PlanningPipeline, planning_pipeline
from platform_planning.planning_events import PlanningCompletedEvent, PlanningFailedEvent, PlanningStartedEvent
from platform_planning.replanning import ReplanningEngine, replanning_engine

logger = logging.getLogger(__name__)


class PlanningEngine:
    """Goal-oriented planning layer — agents plan before acting."""

    def __init__(
        self,
        *,
        pipeline: PlanningPipeline | None = None,
        replanning: ReplanningEngine | None = None,
        metrics: PlanningMetrics | None = None,
        integrations: PlanningIntegrations | None = None,
        config: PlanningEngineConfig | None = None,
    ) -> None:
        self._pipeline = pipeline or planning_pipeline
        self._replanning = replanning or replanning_engine
        self._metrics = metrics or planning_metrics
        self._integrations = integrations or planning_integrations
        self._config = config or DEFAULT_PLANNING_CONFIG
        self._plans: dict[str, ExecutionPlan] = {}

    def reset(self) -> None:
        self._plans.clear()
        self._metrics.reset()

    async def plan(
        self,
        context: PlanningContext,
        *,
        strategy: PlanningStrategy | str | None = None,
    ) -> PlanningResult:
        strategy_key = strategy or self._config.default_strategy
        if isinstance(strategy_key, PlanningStrategy):
            strategy_key = strategy_key.value

        await publish(
            PlanningStartedEvent(
                plan_id="pending",
                goal=context.goal,
                strategy=strategy_key,
                agent_id=context.agent_id,
            )
        )

        try:
            result = await self._pipeline.run(context, strategy=strategy_key)
            self._plans[result.plan.plan_id] = result.plan
            self._metrics.record(result)

            if result.success:
                await publish(
                    PlanningCompletedEvent(
                        plan_id=result.plan.plan_id,
                        step_count=result.plan.step_count,
                        estimated_cost=result.plan.estimated_cost,
                        planning_time_ms=result.planning_time_ms,
                    )
                )
            else:
                await publish(
                    PlanningFailedEvent(plan_id=result.plan.plan_id, error=result.error or "validation failed")
                )

            logger.info(
                "planning_completed plan=%s steps=%d success=%s",
                result.plan.plan_id,
                result.plan.step_count,
                result.success,
            )
            return result

        except Exception as exc:
            raise PlanningError(str(exc)) from exc

    async def plan_for_agent(
        self,
        agent_id: str,
        goal: str,
        *,
        user_id: str | None = None,
        strategy: PlanningStrategy | str | None = None,
        use_reasoning: bool = True,
    ) -> PlanningResult:
        if use_reasoning:
            context = await self._integrations.context_from_reasoning(agent_id, goal, user_id=user_id)
        else:
            context = PlanningContext(goal=goal, agent_id=agent_id, user_id=user_id, permissions=["execute"])
        return await self.plan(context, strategy=strategy)

    async def replan(
        self,
        plan_id: str,
        failed_step_id: str,
        context: PlanningContext,
        *,
        error: str = "",
    ) -> ExecutionPlan:
        plan = self.get_plan(plan_id)
        new_plan = await self._replanning.replan(plan, failed_step_id, context, error=error)
        self._plans[plan_id] = new_plan

        from platform_planning.planning_events import ReplanningTriggeredEvent

        await publish(
            ReplanningTriggeredEvent(
                plan_id=plan_id,
                failed_step_id=failed_step_id,
                replan_count=new_plan.metadata.get("replan_count", 1),
            )
        )
        return new_plan

    async def execute_plan(self, result: PlanningResult) -> dict:
        return await self._integrations.execute_plan_workflow(result.to_dict())

    def get_plan(self, plan_id: str) -> ExecutionPlan:
        if plan_id not in self._plans:
            raise PlanNotFoundError(plan_id)
        return self._plans[plan_id]

    def mark_step_completed(self, plan_id: str, step_id: str, output: dict | None = None) -> None:
        plan = self.get_plan(plan_id)
        self._replanning.mark_step_completed(plan, step_id, output)

    def metrics_summary(self) -> dict:
        return self._metrics.summary()


planning_engine = PlanningEngine()
