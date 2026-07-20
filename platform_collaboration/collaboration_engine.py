# CollaborationEngine — multi-agent coordination, negotiation, and consensus.

from __future__ import annotations

import logging

from events.publisher import publish
from platform_collaboration.collaboration_events import (
    AgentJoinedEvent,
    CollaborationCompletedEvent,
    CollaborationFailedEvent,
    CollaborationStartedEvent,
    ConflictDetectedEvent,
    ConflictResolvedEvent,
    ConsensusReachedEvent,
    TaskDelegatedEvent,
)
from platform_collaboration.config import DEFAULT_COLLABORATION_CONFIG, CollaborationEngineConfig
from platform_collaboration.exceptions import CollaborationError, SessionNotFoundError
from platform_collaboration.integrations import CollaborationIntegrations, collaboration_integrations
from platform_collaboration.metrics import CollaborationMetrics, collaboration_metrics
from platform_collaboration.models import (
    AgentMessage,
    AgentParticipant,
    CollaborationMode,
    CollaborationResult,
    CollaborationSession,
    CollaborationTask,
    ConsensusModel,
    CoordinationStrategy,
    MessageType,
    SharedContext,
)
from platform_collaboration.pipeline import CollaborationPipeline, collaboration_pipeline

logger = logging.getLogger(__name__)


class CollaborationEngine:
    """Multi-agent collaboration layer for shared goals."""

    def __init__(
        self,
        *,
        pipeline: CollaborationPipeline | None = None,
        metrics: CollaborationMetrics | None = None,
        integrations: CollaborationIntegrations | None = None,
        config: CollaborationEngineConfig | None = None,
    ) -> None:
        self._pipeline = pipeline or collaboration_pipeline
        self._metrics = metrics or collaboration_metrics
        self._integrations = integrations or collaboration_integrations
        self._config = config or DEFAULT_COLLABORATION_CONFIG
        self._sessions: dict[str, CollaborationSession] = {}

    def reset(self) -> None:
        self._sessions.clear()
        self._metrics.reset()

    async def collaborate(
        self,
        goal: str,
        agent_ids: list[str],
        *,
        mode: CollaborationMode | str | None = None,
        strategy: CoordinationStrategy | str | None = None,
        consensus_model: ConsensusModel | str | None = None,
        supervisor_id: str | None = None,
        tasks: list[CollaborationTask] | None = None,
        user_id: str | None = None,
    ) -> CollaborationResult:
        mode_key = mode or self._config.default_mode
        if isinstance(mode_key, CollaborationMode):
            mode_key = mode_key.value

        strategy_key = strategy or CoordinationStrategy.SUPERVISOR_DELEGATE
        if isinstance(strategy_key, CoordinationStrategy):
            strategy_key = strategy_key.value

        consensus_key = consensus_model or self._config.default_consensus
        if isinstance(consensus_key, ConsensusModel):
            consensus_key = consensus_key.value

        sup = supervisor_id or (agent_ids[0] if agent_ids else None)
        session = CollaborationSession(
            goal=goal,
            mode=CollaborationMode(mode_key),
            strategy=CoordinationStrategy(strategy_key),
            consensus_model=ConsensusModel(consensus_key),
            supervisor_id=sup,
            shared_context=SharedContext(goal=goal),
        )

        participants = self._integrations.participants_from_registry(agent_ids)
        session.participants.update(participants)

        await publish(
            CollaborationStartedEvent(
                session_id=session.session_id,
                goal=goal,
                mode=mode_key,
                agent_count=len(agent_ids),
            )
        )

        for aid in agent_ids:
            role = session.participants[aid].role.value
            await publish(AgentJoinedEvent(session_id=session.session_id, agent_id=aid, role=role))

        try:
            session = await self._integrations.enrich_with_memory(session, user_id=user_id)
            session = await self._integrations.enrich_with_reasoning(session)
            session = await self._integrations.apply_decision_policy(session)

            if not tasks:
                tasks = await self._integrations.enrich_with_planning(session)

            tools = self._integrations.available_tools()
            result = await self._pipeline.run(session, agent_ids=agent_ids, tasks=tasks, available_tools=tools)

            for neg in result.negotiation_results:
                if neg.owner_id:
                    await publish(
                        TaskDelegatedEvent(
                            session_id=session.session_id,
                            task_id=neg.task_id,
                            agent_id=neg.owner_id,
                        )
                    )

            for cr in result.consensus_results:
                if cr.success:
                    await publish(
                        ConsensusReachedEvent(
                            session_id=session.session_id,
                            decision=cr.decision,
                            confidence=cr.confidence,
                            model=cr.model.value,
                        )
                    )

            if result.conflicts_detected:
                await publish(
                    ConflictDetectedEvent(
                        session_id=session.session_id,
                        conflict_type="detected",
                        description=f"{result.conflicts_detected} conflict(s)",
                    )
                )
            if result.conflicts_resolved:
                await publish(
                    ConflictResolvedEvent(session_id=session.session_id, conflict_type="resolved")
                )

            self._sessions[session.session_id] = result.session
            self._metrics.record(result)

            await publish(
                CollaborationCompletedEvent(
                    session_id=session.session_id,
                    success=result.success,
                    completed_tasks=len(result.completed_tasks),
                    collaboration_time_ms=result.session.collaboration_time_ms,
                )
            )

            await self._integrations.record_learning(session, result.to_dict())

            logger.info(
                "collaboration_completed session=%s tasks=%d success=%s",
                session.session_id,
                len(result.completed_tasks),
                result.success,
            )
            return result

        except Exception as exc:
            await publish(CollaborationFailedEvent(session_id=session.session_id, error=str(exc)))
            raise CollaborationError(str(exc)) from exc

    async def send_message(self, session_id: str, message: AgentMessage) -> AgentMessage:
        session = self.get_session(session_id)
        message.session_id = session_id
        session.messages.append(message)
        return message

    async def broadcast_progress(self, session_id: str, agent_id: str, progress: float, detail: str = "") -> AgentMessage:
        return await self.send_message(
            session_id,
            AgentMessage(
                sender_id=agent_id,
                message_type=MessageType.PROGRESS_UPDATE,
                payload={"progress": progress, "detail": detail},
            ),
        )

    async def share_result(self, session_id: str, agent_id: str, result: dict) -> AgentMessage:
        session = self.get_session(session_id)
        session.shared_context.merge_result(agent_id, result)
        return await self.send_message(
            session_id,
            AgentMessage(
                sender_id=agent_id,
                message_type=MessageType.INTERMEDIATE_RESULT,
                payload=result,
            ),
        )

    def get_session(self, session_id: str) -> CollaborationSession:
        if session_id not in self._sessions:
            raise SessionNotFoundError(session_id)
        return self._sessions[session_id]

    def metrics_summary(self) -> dict:
        return self._metrics.summary()


collaboration_engine = CollaborationEngine()
