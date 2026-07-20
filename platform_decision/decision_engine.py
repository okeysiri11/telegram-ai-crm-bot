# DecisionEngine — evaluate execution alternatives and select optimal strategy.

from __future__ import annotations

import logging
import uuid

from events.publisher import publish
from platform_decision.config import DEFAULT_DECISION_CONFIG, DecisionEngineConfig
from platform_decision.decision_events import DecisionCompletedEvent, DecisionFailedEvent, DecisionStartedEvent
from platform_decision.exceptions import DecisionError
from platform_decision.integrations import DecisionIntegrations, decision_integrations
from platform_decision.metrics import DecisionMetrics, decision_metrics
from platform_decision.models import DecisionContext, DecisionResult, DecisionStrategyType, DecisionTrace
from platform_decision.pipeline import DecisionPipeline, decision_pipeline
from platform_decision.policies import DecisionPolicy, policy_registry

logger = logging.getLogger(__name__)


class DecisionEngine:
    """Reusable decision-making layer for execution strategy selection."""

    def __init__(
        self,
        *,
        pipeline: DecisionPipeline | None = None,
        metrics: DecisionMetrics | None = None,
        integrations: DecisionIntegrations | None = None,
        config: DecisionEngineConfig | None = None,
    ) -> None:
        self._pipeline = pipeline or decision_pipeline
        self._metrics = metrics or decision_metrics
        self._integrations = integrations or decision_integrations
        self._config = config or DEFAULT_DECISION_CONFIG
        self._traces: dict[str, DecisionTrace] = {}

    def reset(self) -> None:
        self._traces.clear()
        self._metrics.reset()
        policy_registry.reset()

    async def decide(
        self,
        context: DecisionContext,
        *,
        strategy: DecisionStrategyType | str | None = None,
        policy_id: str | None = None,
    ) -> DecisionResult:
        strategy_key = strategy or self._config.default_strategy
        if isinstance(strategy_key, DecisionStrategyType):
            strategy_key = strategy_key.value
        policy = policy_id or self._config.default_policy

        context = self._integrations.enrich_tool_availability(context)
        context = self._integrations.enrich_agent_availability(context)
        context = self._integrations.enrich_memory_preferences(context)

        if len(context.candidates) > self._config.max_candidates:
            context.candidates = context.candidates[: self._config.max_candidates]

        decision_id = str(uuid.uuid4())
        await publish(
            DecisionStartedEvent(
                decision_id=decision_id,
                candidate_count=len(context.candidates),
                strategy=strategy_key,
                policy_id=policy,
                agent_id=context.agent_id,
            )
        )

        try:
            result = await self._pipeline.run(context, strategy=strategy_key, policy_id=policy)
            if result.confidence < self._config.min_confidence_threshold and context.candidates:
                fallback = await self._pipeline.run(
                    context,
                    strategy=DecisionStrategyType.FALLBACK.value,
                    policy_id=policy,
                )
                fallback.trace.add_step("fallback", f"Low confidence ({result.confidence}%), used fallback strategy")
                result = fallback

            self._traces[result.decision_id] = result.trace  # type: ignore[assignment]
            self._metrics.record(result)

            await publish(
                DecisionCompletedEvent(
                    decision_id=result.decision_id,
                    selected_candidate_id=result.selected.candidate_id,
                    confidence=result.confidence,
                    strategy=result.strategy.value,
                    policy_id=result.policy_id,
                    decision_time_ms=result.decision_time_ms,
                    alternatives_count=len(result.alternatives),
                )
            )

            logger.info(
                "decision_completed id=%s selected=%s confidence=%.1f",
                result.decision_id,
                result.selected.candidate_id,
                result.confidence,
            )
            return result

        except Exception as exc:
            await publish(
                DecisionFailedEvent(
                    decision_id=decision_id,
                    error=str(exc),
                    strategy=strategy_key if isinstance(strategy_key, str) else "",
                )
            )
            raise DecisionError(str(exc)) from exc

    async def decide_for_agent(
        self,
        agent_id: str,
        request: str,
        *,
        user_id: str | None = None,
        strategy: DecisionStrategyType | str | None = None,
        policy_id: str | None = None,
        use_planning: bool = True,
    ) -> DecisionResult:
        if use_planning:
            context = await self._integrations.context_from_planning(agent_id, request, user_id=user_id)
        else:
            context = await self._integrations.context_from_reasoning(agent_id, request, user_id=user_id)

        if not context.candidates:
            from platform_agents.registry import agent_registry

            try:
                agent = agent_registry.get(agent_id)
                caps = list(agent.metadata().capabilities)
            except Exception:
                caps = ["general"]
            context.candidates = self._integrations.candidates_from_capabilities(caps, agent_id=agent_id)

        return await self.decide(context, strategy=strategy, policy_id=policy_id)

    async def execute_selected(self, result: DecisionResult) -> dict:
        return await self._integrations.execute_selected_workflow(result.to_dict())

    def get_trace(self, decision_id: str) -> DecisionTrace | None:
        return self._traces.get(decision_id)

    def register_policy(self, policy: DecisionPolicy) -> None:
        policy_registry.register(policy)

    def metrics_summary(self) -> dict:
        return self._metrics.summary()


decision_engine = DecisionEngine()
