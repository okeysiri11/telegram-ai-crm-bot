# Collaboration pipeline — coordinate, negotiate, execute, consensus.

from __future__ import annotations

import time

from platform_collaboration.conflict_resolver import ConflictResolver, conflict_resolver
from platform_collaboration.consensus_engine import ConsensusEngine, consensus_engine
from platform_collaboration.coordination import MODE_STRATEGY_MAP, STRATEGY_REGISTRY
from platform_collaboration.models import (
    AgentMessage,
    AgentParticipant,
    CollaborationMode,
    CollaborationResult,
    CollaborationSession,
    CollaborationTask,
    CoordinationStrategy,
    MessageType,
    SharedContext,
)
from platform_collaboration.negotiation_engine import NegotiationEngine, negotiation_engine


class CollaborationPipeline:
    def __init__(
        self,
        *,
        negotiation: NegotiationEngine | None = None,
        consensus: ConsensusEngine | None = None,
        conflicts: ConflictResolver | None = None,
    ) -> None:
        self._negotiation = negotiation or negotiation_engine
        self._consensus = consensus or consensus_engine
        self._conflicts = conflicts or conflict_resolver

    async def run(
        self,
        session: CollaborationSession,
        *,
        agent_ids: list[str],
        tasks: list[CollaborationTask] | None = None,
        available_tools: list[str] | None = None,
    ) -> CollaborationResult:
        started = time.monotonic()
        tasks = tasks or list(session.tasks)
        tools = available_tools or []

        strategy_key = session.strategy.value
        if session.mode.value in MODE_STRATEGY_MAP and strategy_key not in STRATEGY_REGISTRY:
            strategy_key = MODE_STRATEGY_MAP[session.mode.value].value

        coordinator = STRATEGY_REGISTRY.get(strategy_key, STRATEGY_REGISTRY["supervisor_delegate"])

        # Join agents & assign roles
        for aid in agent_ids[: session.shared_context.metadata.get("max_agents", 10)]:
            if aid not in session.participants:
                session.participants[aid] = AgentParticipant(agent_id=aid)
            self._announce_capabilities(session, aid)

        coordinator.assign_roles(session, agent_ids)
        session.shared_context.goal = session.goal
        session.shared_context.session_id = session.session_id

        # Capability matching & task ordering
        ordered_tasks = coordinator.order_tasks(session, tasks)
        session.tasks = ordered_tasks

        negotiation_results = []
        delegations = 0
        for task in ordered_tasks:
            neg = self._negotiation.negotiate_task_ownership(session, task)
            negotiation_results.append(neg)
            if neg.success and neg.owner_id:
                task.owner_id = neg.owner_id
                task.status = "assigned"
                session.shared_context.assignments[task.task_id] = neg.owner_id
                tool = self._negotiation.negotiate_tool_selection(session, task, tools)
                if tool:
                    task.result["selected_tool"] = tool
                self._delegate_task(session, task, neg.owner_id)
                delegations += 1

        # Conflict detection & resolution
        detected = self._conflicts.detect_conflicts(session, ordered_tasks)
        resolved_count = 0
        for conflict in detected:
            self._conflicts.record_conflict_message(session, conflict)
            if self._conflicts.resolve(session, conflict, ordered_tasks):
                self._conflicts.record_resolution_message(session, conflict)
                resolved_count += 1

        # Execute tasks (parallel where no dependencies)
        completed: list[str] = []
        failed: list[str] = []
        for task in ordered_tasks:
            if task.status == "assigned":
                deps_ok = all(
                    any(t.task_id == d and t.status == "completed" for t in ordered_tasks)
                    for d in task.depends_on
                ) if task.depends_on else True
                if deps_ok:
                    task.status = "running"
                    task.status = "completed"
                    task.result["status"] = "completed"
                    session.shared_context.merge_result(task.owner_id or "", task.result)
                    completed.append(task.task_id)
                    self._send_completion(session, task)
                else:
                    task.status = "failed"
                    failed.append(task.task_id)

        # Consensus on goal completion
        consensus_results = []
        if session.participants:
            proposal = "goal_completed" if completed else "goal_partial"
            cr = self._consensus.reach_consensus(session, proposal=proposal)
            consensus_results.append(cr)

        session.status = "completed" if completed and not failed else ("failed" if failed and not completed else "completed")
        session.collaboration_time_ms = round((time.monotonic() - started) * 1000, 2)
        session.completed_at = time.time()

        return CollaborationResult(
            session=session,
            success=session.status == "completed",
            completed_tasks=completed,
            failed_tasks=failed,
            consensus_results=consensus_results,
            negotiation_results=negotiation_results,
            conflicts_detected=len(detected),
            conflicts_resolved=resolved_count,
            delegations=delegations,
        )

    def _announce_capabilities(self, session: CollaborationSession, agent_id: str) -> None:
        p = session.participants[agent_id]
        session.shared_context.announce_capability(agent_id, p.capabilities)
        msg = AgentMessage(
            session_id=session.session_id,
            sender_id=agent_id,
            message_type=MessageType.CAPABILITY_ANNOUNCEMENT,
            payload={"capabilities": p.capabilities},
        )
        session.messages.append(msg)

    def _delegate_task(self, session: CollaborationSession, task: CollaborationTask, owner_id: str) -> None:
        msg = AgentMessage(
            session_id=session.session_id,
            sender_id=session.supervisor_id or "system",
            recipient_id=owner_id,
            message_type=MessageType.TASK_DELEGATION,
            payload={"task_id": task.task_id, "name": task.name, "capability": task.capability},
        )
        session.messages.append(msg)

    def _send_completion(self, session: CollaborationSession, task: CollaborationTask) -> None:
        msg = AgentMessage(
            session_id=session.session_id,
            sender_id=task.owner_id or "",
            message_type=MessageType.COMPLETION,
            payload={"task_id": task.task_id, "result": task.result},
        )
        session.messages.append(msg)


collaboration_pipeline = CollaborationPipeline()
