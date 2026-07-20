# Integration bridges — Reasoning, Planning, Decision, Workflow, Memory, Tools, Agents, Orchestrator.

from __future__ import annotations

import logging
from typing import Any

from platform_learning.models import FeedbackCategory, FeedbackRecord, FeedbackSentiment, FeedbackSource, LearningContext

logger = logging.getLogger(__name__)


class LearningIntegrations:
    @staticmethod
    async def collect_from_platform(agent_id: str | None = None) -> LearningContext:
        history: dict[str, Any] = {
            "workflows": [],
            "decisions": [],
            "planning": [],
            "reasoning": [],
            "tools": [],
            "tasks": [],
        }

        try:
            from platform_decision import decision_engine

            summary = decision_engine.metrics_summary()
            if summary.get("decisions", 0) > 0:
                history["decisions"].append({
                    "decision_id": "aggregate",
                    "success": summary.get("success_rate", 0) > 0.5,
                    "avg_confidence": summary.get("avg_confidence", 0),
                })
        except Exception:
            logger.debug("decision_engine unavailable for learning")

        try:
            from platform_planning import planning_engine

            summary = planning_engine.metrics_summary()
            if summary.get("plans", 0) > 0:
                history["planning"].append({
                    "plan_id": "aggregate",
                    "success": summary.get("plan_success_rate", 0) > 0.5,
                    "avg_steps": summary.get("avg_plan_size", 0),
                })
        except Exception:
            logger.debug("planning_engine unavailable for learning")

        try:
            from platform_reasoning.metrics import reasoning_metrics

            summary = reasoning_metrics.summary()
            if summary.get("sessions", 0) > 0:
                history["reasoning"].append({
                    "session_id": "aggregate",
                    "success": summary.get("avg_confidence", 0) > 50,
                })
        except Exception:
            logger.debug("reasoning_engine unavailable for learning")

        try:
            from platform_workflow.metrics import workflow_metrics

            summary = workflow_metrics.summary()
            if summary.get("executions", 0) > 0:
                history["workflows"].append({
                    "workflow_id": "aggregate",
                    "success": summary.get("success_rate", 0) > 0.5,
                })
        except Exception:
            logger.debug("workflow_engine unavailable for learning")

        try:
            from platform_tools.metrics import tool_metrics

            summary = tool_metrics.summary()
            by_tool = summary.get("by_tool", {})
            for tool_id in by_tool:
                history["tools"].append({"tool_id": tool_id, "success": True, "count": by_tool[tool_id].get("usage_count", 1)})
        except Exception:
            logger.debug("tool_metrics unavailable for learning")

        return LearningContext(agent_id=agent_id, execution_history=history)

    @staticmethod
    def feedback_from_workflow(workflow_id: str, *, success: bool, agent_id: str | None = None) -> FeedbackRecord:
        from platform_learning.feedback_collector import feedback_collector

        return feedback_collector.collect_workflow_result(workflow_id, success=success, agent_id=agent_id)

    @staticmethod
    def feedback_from_decision(decision_dict: dict[str, Any], *, agent_id: str | None = None) -> FeedbackRecord:
        success = decision_dict.get("success", True)
        return FeedbackRecord(
            sentiment=FeedbackSentiment.POSITIVE if success else FeedbackSentiment.NEGATIVE,
            confidence_score=decision_dict.get("confidence", 50.0),
            category=FeedbackCategory.DECISION,
            source=FeedbackSource.SYSTEM_EVENT,
            message=f"Decision {decision_dict.get('decision_id', '')} outcome",
            agent_id=agent_id,
            metadata=decision_dict,
        )

    @staticmethod
    def feedback_from_planning(plan_dict: dict[str, Any], *, agent_id: str | None = None) -> FeedbackRecord:
        success = plan_dict.get("success", True)
        return FeedbackRecord(
            sentiment=FeedbackSentiment.POSITIVE if success else FeedbackSentiment.NEGATIVE,
            confidence_score=80.0,
            category=FeedbackCategory.PLANNING,
            source=FeedbackSource.SYSTEM_EVENT,
            message=f"Planning {plan_dict.get('plan_id', '')} outcome",
            agent_id=agent_id,
            metadata=plan_dict,
        )

    @staticmethod
    async def enrich_with_memory(context: LearningContext, *, user_id: str | None = None) -> LearningContext:
        try:
            from platform_memory.context_assembler import ContextAssembler

            assembler = ContextAssembler()
            result = assembler.assemble(user_id or context.user_id or "default", query="learning")
            if result:
                context.metadata["memory"] = result.to_dict() if hasattr(result, "to_dict") else {}
        except Exception:
            logger.debug("memory_engine unavailable for learning")
        return context

    @staticmethod
    def orchestrator_insights(result_dict: dict[str, Any]) -> dict[str, Any]:
        return {
            "session_id": result_dict.get("session", {}).get("session_id"),
            "recommendations_count": len(result_dict.get("recommendations", [])),
            "failure_patterns": len(result_dict.get("failure_patterns", [])),
            "insights": result_dict.get("insights", {}),
        }

    @staticmethod
    def agent_registry_feedback(agent_id: str) -> FeedbackRecord | None:
        try:
            from platform_agents.registry import agent_registry

            agent = agent_registry.get(agent_id)
            meta = agent.metadata()
            sentiment = FeedbackSentiment.POSITIVE if meta.enabled else FeedbackSentiment.NEUTRAL
            return FeedbackRecord(
                sentiment=sentiment,
                confidence_score=85.0,
                category=FeedbackCategory.AGENT,
                source=FeedbackSource.AGENT_SELF_EVAL,
                message=f"Agent {agent_id} registry status",
                agent_id=agent_id,
            )
        except Exception:
            return None


learning_integrations = LearningIntegrations()
