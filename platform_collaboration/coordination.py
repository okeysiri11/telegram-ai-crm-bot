# Coordination strategies — role assignment, parallel, hierarchical execution.

from __future__ import annotations

from abc import ABC, abstractmethod

from platform_collaboration.models import (
    AgentParticipant,
    CollaborationMode,
    CollaborationRole,
    CollaborationSession,
    CollaborationTask,
    CoordinationStrategy,
)


class BaseCoordinationStrategy(ABC):
    strategy_id: CoordinationStrategy

    @abstractmethod
    def assign_roles(self, session: CollaborationSession, agent_ids: list[str]) -> None: ...

    @abstractmethod
    def order_tasks(self, session: CollaborationSession, tasks: list[CollaborationTask]) -> list[CollaborationTask]: ...


class SupervisorDelegateStrategy(BaseCoordinationStrategy):
    strategy_id = CoordinationStrategy.SUPERVISOR_DELEGATE

    def assign_roles(self, session, agent_ids) -> None:
        if session.supervisor_id and session.supervisor_id in agent_ids:
            session.participants[session.supervisor_id].role = CollaborationRole.SUPERVISOR
        for aid in agent_ids:
            if aid != session.supervisor_id:
                p = session.participants.setdefault(
                    aid, AgentParticipant(agent_id=aid, role=CollaborationRole.WORKER)
                )
                p.role = CollaborationRole.WORKER

    def order_tasks(self, session, tasks) -> list[CollaborationTask]:
        return sorted(tasks, key=lambda t: (-t.priority, t.task_id))


class PeerConsensusStrategy(BaseCoordinationStrategy):
    strategy_id = CoordinationStrategy.PEER_CONSENSUS

    def assign_roles(self, session, agent_ids) -> None:
        for aid in agent_ids:
            p = session.participants.setdefault(aid, AgentParticipant(agent_id=aid))
            p.role = CollaborationRole.PEER

    def order_tasks(self, session, tasks) -> list[CollaborationTask]:
        return sorted(tasks, key=lambda t: t.task_id)


class ParallelStrategy(BaseCoordinationStrategy):
    strategy_id = CoordinationStrategy.PARALLEL

    def assign_roles(self, session, agent_ids) -> None:
        for aid in agent_ids:
            session.participants.setdefault(
                aid, AgentParticipant(agent_id=aid, role=CollaborationRole.WORKER)
            )

    def order_tasks(self, session, tasks) -> list[CollaborationTask]:
        independent = [t for t in tasks if not t.depends_on]
        dependent = [t for t in tasks if t.depends_on]
        return independent + dependent


class CapabilityMatchStrategy(BaseCoordinationStrategy):
    strategy_id = CoordinationStrategy.CAPABILITY_MATCH

    def assign_roles(self, session, agent_ids) -> None:
        for aid in agent_ids:
            p = session.participants.setdefault(
                aid, AgentParticipant(agent_id=aid, role=CollaborationRole.SPECIALIST)
            )
            p.role = CollaborationRole.SPECIALIST

    def order_tasks(self, session, tasks) -> list[CollaborationTask]:
        def match_score(task: CollaborationTask) -> float:
            if not task.capability:
                return 0.0
            return sum(
                1 for p in session.participants.values() if task.capability in p.capabilities
            )
        return sorted(tasks, key=lambda t: -match_score(t))


class RoleBasedStrategy(BaseCoordinationStrategy):
    strategy_id = CoordinationStrategy.ROLE_BASED

    def assign_roles(self, session, agent_ids) -> None:
        if not agent_ids:
            return
        session.participants.setdefault(
            agent_ids[0],
            AgentParticipant(agent_id=agent_ids[0], role=CollaborationRole.COORDINATOR),
        ).role = CollaborationRole.COORDINATOR
        for aid in agent_ids[1:]:
            session.participants.setdefault(
                aid, AgentParticipant(agent_id=aid, role=CollaborationRole.WORKER)
            ).role = CollaborationRole.WORKER

    def order_tasks(self, session, tasks) -> list[CollaborationTask]:
        return tasks


class SequentialStrategy(BaseCoordinationStrategy):
    strategy_id = CoordinationStrategy.SEQUENTIAL

    def assign_roles(self, session, agent_ids) -> None:
        SupervisorDelegateStrategy().assign_roles(session, agent_ids)

    def order_tasks(self, session, tasks) -> list[CollaborationTask]:
        ordered: list[CollaborationTask] = []
        remaining = list(tasks)
        completed: set[str] = set()
        while remaining:
            ready = [t for t in remaining if all(d in completed for d in t.depends_on)]
            if not ready:
                ordered.extend(remaining)
                break
            for t in ready:
                ordered.append(t)
                completed.add(t.task_id)
                remaining.remove(t)
        return ordered


MODE_STRATEGY_MAP: dict[str, CoordinationStrategy] = {
    CollaborationMode.ONE_TO_ONE.value: CoordinationStrategy.SEQUENTIAL,
    CollaborationMode.ONE_TO_MANY.value: CoordinationStrategy.SUPERVISOR_DELEGATE,
    CollaborationMode.MANY_TO_MANY.value: CoordinationStrategy.PEER_CONSENSUS,
    CollaborationMode.HIERARCHICAL.value: CoordinationStrategy.ROLE_BASED,
    CollaborationMode.PEER_TO_PEER.value: CoordinationStrategy.PEER_CONSENSUS,
    CollaborationMode.SUPERVISOR_WORKER.value: CoordinationStrategy.SUPERVISOR_DELEGATE,
}

STRATEGY_REGISTRY: dict[str, BaseCoordinationStrategy] = {
    "role_based": RoleBasedStrategy(),
    "capability_match": CapabilityMatchStrategy(),
    "parallel": ParallelStrategy(),
    "sequential": SequentialStrategy(),
    "supervisor_delegate": SupervisorDelegateStrategy(),
    "peer_consensus": PeerConsensusStrategy(),
}
