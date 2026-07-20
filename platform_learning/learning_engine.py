# LearningEngine — continuous improvement from execution history and feedback.

from __future__ import annotations

import logging

from events.publisher import publish
from platform_learning.config import DEFAULT_LEARNING_CONFIG, LearningEngineConfig
from platform_learning.exceptions import LearningError, SessionNotFoundError
from platform_learning.experience_store import experience_store
from platform_learning.feedback_collector import feedback_collector
from platform_learning.integrations import LearningIntegrations, learning_integrations
from platform_learning.learning_events import (
    FeedbackReceivedEvent,
    LearningCycleCompletedEvent,
    LearningCycleStartedEvent,
    LearningFailedEvent,
    RecommendationGeneratedEvent,
)
from platform_learning.metrics import LearningMetrics, learning_metrics
from platform_learning.models import FeedbackRecord, LearningContext, LearningResult, LearningSession
from platform_learning.pipeline import LearningPipeline, learning_pipeline
from platform_learning.recommendation_engine import recommendation_engine

logger = logging.getLogger(__name__)


class LearningEngine:
    """Reusable learning subsystem for continuous agent improvement."""

    def __init__(
        self,
        *,
        pipeline: LearningPipeline | None = None,
        metrics: LearningMetrics | None = None,
        integrations: LearningIntegrations | None = None,
        config: LearningEngineConfig | None = None,
    ) -> None:
        self._pipeline = pipeline or learning_pipeline
        self._metrics = metrics or learning_metrics
        self._integrations = integrations or learning_integrations
        self._config = config or DEFAULT_LEARNING_CONFIG
        self._sessions: dict[str, LearningSession] = {}

    def reset(self) -> None:
        self._sessions.clear()
        self._metrics.reset()
        experience_store.reset()
        feedback_collector.reset()
        recommendation_engine.reset()

    async def learn(self, context: LearningContext) -> LearningResult:
        session_id = context.session_id or LearningSession().session_id
        context.session_id = session_id

        await publish(LearningCycleStartedEvent(session_id=session_id, agent_id=context.agent_id))

        try:
            context = await self._integrations.enrich_with_memory(context, user_id=context.user_id)
            result = await self._pipeline.run(context)
            self._sessions[session_id] = result.session
            self._metrics.record(result)

            for rec in result.recommendations:
                await publish(
                    RecommendationGeneratedEvent(
                        session_id=session_id,
                        recommendation_id=rec.recommendation_id,
                        recommendation_type=rec.recommendation_type.value,
                    )
                )

            patterns = len(result.success_patterns) + len(result.failure_patterns)
            await publish(
                LearningCycleCompletedEvent(
                    session_id=session_id,
                    recommendations_count=len(result.recommendations),
                    patterns_detected=patterns,
                    cycle_time_ms=result.session.cycle_time_ms,
                )
            )

            logger.info(
                "learning_completed session=%s patterns=%d recommendations=%d",
                session_id,
                patterns,
                len(result.recommendations),
            )
            return result

        except Exception as exc:
            await publish(LearningFailedEvent(session_id=session_id, error=str(exc)))
            raise LearningError(str(exc)) from exc

    async def collect_feedback(self, record: FeedbackRecord) -> FeedbackRecord:
        collected = feedback_collector.collect(record)
        await publish(
            FeedbackReceivedEvent(
                feedback_id=collected.feedback_id,
                source=collected.source.value,
                sentiment=collected.sentiment.value,
                agent_id=collected.agent_id,
            )
        )
        return collected

    async def learn_for_agent(self, agent_id: str, *, user_id: str | None = None) -> LearningResult:
        context = await self._integrations.collect_from_platform(agent_id=agent_id)
        context.agent_id = agent_id
        context.user_id = user_id

        agent_fb = self._integrations.agent_registry_feedback(agent_id)
        if agent_fb:
            context.feedback.append(agent_fb)

        return await self.learn(context)

    def accept_recommendation(self, recommendation_id: str) -> None:
        recommendation_engine.accept(recommendation_id)
        summary = self._metrics.summary()
        summary["recommendation_acceptance_rate"] = recommendation_engine.acceptance_rate()

    def reject_recommendation(self, recommendation_id: str) -> None:
        recommendation_engine.reject(recommendation_id)

    def get_session(self, session_id: str) -> LearningSession:
        if session_id not in self._sessions:
            raise SessionNotFoundError(session_id)
        return self._sessions[session_id]

    def get_insights(self, session_id: str) -> dict:
        session = self.get_session(session_id)
        return dict(session.insights)

    def metrics_summary(self) -> dict:
        summary = self._metrics.summary()
        summary["recommendation_acceptance_rate"] = recommendation_engine.acceptance_rate()
        return summary


learning_engine = LearningEngine()
