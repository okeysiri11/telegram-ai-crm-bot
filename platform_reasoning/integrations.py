# Integration bridges — connect reasoning to platform layers without modifying them.

from __future__ import annotations

import logging
from typing import Any

from platform_reasoning.models import ReasoningContext

logger = logging.getLogger(__name__)


class ReasoningIntegrations:
    """Optional bridges to Memory, Workflow, Agent Registry, Orchestrator, Tools."""

    @staticmethod
    def context_from_agent(agent_id: str, request: str, *, user_id: str | None = None) -> ReasoningContext:
        capabilities: list[str] = []
        available_tools: list[str] = []

        try:
            from platform_agents.registry import agent_registry

            agent = agent_registry.get(agent_id)
            capabilities = list(agent.metadata().capabilities)
        except Exception:
            logger.debug("agent_registry unavailable for reasoning context")

        try:
            from platform_tools.agent_bridge import agent_tool_bridge

            available_tools = agent_tool_bridge.get_agent_tools(agent_id)
        except Exception:
            logger.debug("tool_bridge unavailable for reasoning context")

        return ReasoningContext(
            request=request,
            agent_id=agent_id,
            user_id=user_id,
            capabilities=capabilities,
            available_tools=available_tools,
        )

    @staticmethod
    def enrich_with_memory(context: ReasoningContext, *, user_id: str | None = None) -> ReasoningContext:
        memory_context: dict[str, Any] = {}
        try:
            uid = user_id or context.user_id
            if uid:
                memory_context = {"user_id": uid, "facts": [], "source": "platform_memory"}
        except Exception:
            pass
        context.memory_context = memory_context
        return context

    @staticmethod
    def enrich_with_workflow(context: ReasoningContext, workflow_id: str) -> ReasoningContext:
        context.workflow_context = {"workflow_id": workflow_id, "source": "platform_workflow"}
        return context

    @staticmethod
    def apply_to_orchestrator(result_dict: dict[str, Any]) -> dict[str, Any]:
        """Produce orchestrator-ready routing hints from reasoning result."""
        return {
            "capability": result_dict.get("recommended_capability"),
            "confidence": result_dict.get("confidence", {}).get("overall", 0),
            "plan": result_dict.get("plan", []),
            "missing_information": result_dict.get("missing_information", []),
        }


reasoning_integrations = ReasoningIntegrations()
