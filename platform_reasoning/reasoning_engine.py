# ReasoningEngine — central reasoning layer for all AI agents.

from __future__ import annotations

import logging
import time

from events.publisher import publish
from platform_reasoning.config import DEFAULT_REASONING_CONFIG, ReasoningEngineConfig
from platform_reasoning.exceptions import ReasoningError, ReasoningSessionNotFoundError
from platform_reasoning.integrations import ReasoningIntegrations, reasoning_integrations
from platform_reasoning.metrics import ReasoningMetrics, reasoning_metrics
from platform_reasoning.models import ReasoningContext, ReasoningResult, ReasoningSession, ReasoningStrategy
from platform_reasoning.pipeline import ReasoningPipeline, reasoning_pipeline
from platform_reasoning.reasoning_events import (
    ReasoningCompletedEvent,
    ReasoningFailedEvent,
    ReasoningStartedEvent,
)

logger = logging.getLogger(__name__)


class ReasoningEngine:
    """Reusable reasoning layer — agents think before acting."""

    def __init__(
        self,
        *,
        pipeline: ReasoningPipeline | None = None,
        metrics: ReasoningMetrics | None = None,
        integrations: ReasoningIntegrations | None = None,
        config: ReasoningEngineConfig | None = None,
    ) -> None:
        self._pipeline = pipeline or reasoning_pipeline
        self._metrics = metrics or reasoning_metrics
        self._integrations = integrations or reasoning_integrations
        self._config = config or DEFAULT_REASONING_CONFIG
        self._sessions: dict[str, ReasoningSession] = {}

    def reset(self) -> None:
        self._sessions.clear()
        self._metrics.reset()

    async def reason(
        self,
        context: ReasoningContext,
        *,
        strategy: ReasoningStrategy | str | None = None,
    ) -> ReasoningResult:
        strategy_key = strategy or self._config.default_strategy
        if isinstance(strategy_key, ReasoningStrategy):
            strategy_key = strategy_key.value

        session = ReasoningSession(context=context, strategy=ReasoningStrategy(strategy_key))
        session.status = "running"
        self._sessions[session.session_id] = session

        await publish(
            ReasoningStartedEvent(
                session_id=session.session_id,
                strategy=strategy_key,
                agent_id=context.agent_id,
                request_preview=context.request[:120],
            )
        )

        try:
            pipeline = ReasoningPipeline(debug=self._config.debug_mode)
            result = await pipeline.run(context, strategy=strategy_key)
            result.session_id = session.session_id

            session.result = result
            session.status = "completed"
            session.completed_at = time.time()
            self._metrics.record(result)

            await publish(
                ReasoningCompletedEvent(
                    session_id=session.session_id,
                    strategy=strategy_key,
                    intent=result.intent,
                    overall_confidence=result.confidence.overall,
                    execution_time_ms=result.execution_time_ms,
                    reasoning_depth=result.trace.depth,
                )
            )
            logger.info(
                "reasoning_completed session=%s intent=%s confidence=%.1f",
                session.session_id,
                result.intent,
                result.confidence.overall,
            )
            return result

        except Exception as exc:
            session.status = "failed"
            await publish(
                ReasoningFailedEvent(
                    session_id=session.session_id,
                    strategy=strategy_key,
                    error=str(exc),
                    agent_id=context.agent_id,
                )
            )
            logger.exception("reasoning_failed session=%s", session.session_id)
            raise ReasoningError(str(exc)) from exc

    async def reason_for_agent(
        self,
        agent_id: str,
        request: str,
        *,
        user_id: str | None = None,
        strategy: ReasoningStrategy | str | None = None,
    ) -> ReasoningResult:
        context = self._integrations.context_from_agent(agent_id, request, user_id=user_id)
        context = self._integrations.enrich_with_memory(context, user_id=user_id)
        return await self.reason(context, strategy=strategy)

    def get_session(self, session_id: str) -> ReasoningSession:
        if session_id not in self._sessions:
            raise ReasoningSessionNotFoundError(session_id)
        return self._sessions[session_id]

    def list_sessions(self) -> list[ReasoningSession]:
        return list(self._sessions.values())

    def metrics_summary(self) -> dict:
        return self._metrics.summary()


reasoning_engine = ReasoningEngine()
