# Integration bridges — Reasoning, Planning, Decision, Learning, Workflow, Tools, Agents, Orchestrator, Memory.

from __future__ import annotations

import logging
from typing import Any

from platform_collaboration.models import (
    AgentParticipant,
    CollaborationMode,
    CollaborationSession,
    CollaborationTask,
    SharedContext,
)

logger = logging.getLogger(__name__)


class CollaborationIntegrations:
    @staticmethod
    def participants_from_registry(agent_ids: list[str]) -> dict[str, AgentParticipant]:
        participants: dict[str, AgentParticipant] = {}
        for aid in agent_ids:
            caps: list[str] = []
            try:
                from platform_agents.registry import agent_registry

                agent = agent_registry.get(aid)
                meta = agent.metadata()
                caps = list(meta.capabilities)
            except Exception:
                logger.debug("agent_registry unavailable for %s", aid)
            participants[aid] = AgentParticipant(agent_id=aid, capabilities=caps, confidence=75.0)
        return participants

    @staticmethod
    async def enrich_with_reasoning(session: CollaborationSession) -> CollaborationSession:
        try:
            from platform_reasoning import reasoning_engine
            from platform_reasoning.integrations import reasoning_integrations
            from platform_reasoning.models import ReasoningContext

            if session.supervisor_id:
                ctx = reasoning_integrations.context_from_agent(session.supervisor_id, session.goal)
                result = await reasoning_engine.reason(ctx)
                session.shared_context.data["reasoning"] = result.to_dict()
        except Exception:
            logger.debug("reasoning_engine unavailable for collaboration")
        return session

    @staticmethod
    async def enrich_with_planning(session: CollaborationSession) -> list[CollaborationTask]:
        tasks: list[CollaborationTask] = []
        try:
            from platform_planning import planning_engine

            if session.supervisor_id:
                plan_result = await planning_engine.plan_for_agent(session.supervisor_id, session.goal)
                for step in plan_result.plan.steps:
                    tasks.append(CollaborationTask(
                        name=step.name,
                        capability=step.capability,
                        priority=50.0,
                        depends_on=list(step.depends_on),
                    ))
                session.shared_context.data["planning"] = plan_result.to_dict()
        except Exception:
            logger.debug("planning_engine unavailable for collaboration")
        return tasks

    @staticmethod
    async def apply_decision_policy(session: CollaborationSession) -> CollaborationSession:
        try:
            from platform_decision import decision_engine
            from platform_decision.integrations import decision_integrations

            if session.supervisor_id:
                result = await decision_engine.decide_for_agent(
                    session.supervisor_id, session.goal, use_planning=False
                )
                session.shared_context.data["decision"] = result.to_dict()
        except Exception:
            logger.debug("decision_engine unavailable for collaboration")
        return session

    @staticmethod
    async def record_learning(session: CollaborationSession, result_dict: dict[str, Any]) -> None:
        try:
            from platform_learning import learning_engine
            from platform_learning.models import FeedbackCategory, FeedbackRecord, FeedbackSentiment, FeedbackSource, LearningContext

            fb = FeedbackRecord(
                sentiment=FeedbackSentiment.POSITIVE if result_dict.get("success") else FeedbackSentiment.NEGATIVE,
                category=FeedbackCategory.AGENT,
                source=FeedbackSource.SYSTEM_EVENT,
                message=f"Collaboration {session.session_id} completed",
                agent_id=session.supervisor_id,
            )
            ctx = LearningContext(agent_id=session.supervisor_id, feedback=[fb])
            await learning_engine.learn(ctx)
        except Exception:
            logger.debug("learning_engine unavailable for collaboration")

    @staticmethod
    async def execute_workflow(session: CollaborationSession, tasks: list[CollaborationTask]) -> dict[str, Any]:
        try:
            from platform_workflow.models import WorkflowStep
            from platform_workflow import workflow_engine

            steps = [
                WorkflowStep(
                    step_id=t.task_id,
                    name=t.name,
                    capability=t.capability,
                    assignee_id=t.owner_id,
                )
                for t in tasks if t.status == "completed"
            ]
            if not steps:
                return {"executed": False, "reason": "no completed tasks"}
            wf = await workflow_engine.create_workflow(f"Collaboration {session.session_id[:8]}", steps)
            executed = await workflow_engine.execute_workflow(wf.workflow_id)
            return {"executed": True, "workflow_id": wf.workflow_id, "status": executed.status.value}
        except Exception:
            logger.debug("workflow_engine unavailable")
            return {"executed": False}

    @staticmethod
    def available_tools() -> list[str]:
        try:
            from platform_tools.registry import tool_registry

            return [t.tool_id for t in tool_registry.list_tools()]
        except Exception:
            return []

    @staticmethod
    def orchestrator_routing(session: CollaborationSession) -> dict[str, Any]:
        return {
            "session_id": session.session_id,
            "goal": session.goal,
            "mode": session.mode.value,
            "supervisor_id": session.supervisor_id,
            "participants": list(session.participants.keys()),
            "task_count": len(session.tasks),
        }

    @staticmethod
    async def enrich_with_memory(session: CollaborationSession, *, user_id: str | None = None) -> CollaborationSession:
        try:
            from platform_memory.context_assembler import ContextAssembler

            assembler = ContextAssembler()
            result = assembler.assemble(user_id or "default", query=session.goal)
            if result:
                session.shared_context.data["memory"] = result.to_dict() if hasattr(result, "to_dict") else {}
        except Exception:
            logger.debug("memory_engine unavailable for collaboration")
        return session


collaboration_integrations = CollaborationIntegrations()
