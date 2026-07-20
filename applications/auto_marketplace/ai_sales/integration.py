# Platform Core integration bridge for AI Sales — no platform modifications.

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class AISalesPlatformBridge:
    """Wraps Memory, Reasoning, Planning, Decision, Learning, Workflow, Collaboration engines."""

    @staticmethod
    async def remember_conversation(customer_id: str, session_id: str, content: dict[str, Any]) -> None:
        try:
            from platform_memory import memory_service

            await memory_service.remember_session_memory(
                session_id=f"ai-sales:{customer_id}:{session_id}",
                content=json.dumps(content),
            )
        except Exception:
            logger.debug("memory engine unavailable")

    @staticmethod
    async def recall_customer_context(customer_id: str) -> dict[str, Any]:
        try:
            from applications.auto_marketplace.integrations.platform_bridge import platform_bridge

            await platform_bridge.store_customer_context(customer_id, {"source": "ai_sales"})
        except Exception:
            pass
        return {"customer_id": customer_id}

    @staticmethod
    async def reason(query: str, metadata: dict[str, Any]) -> dict[str, Any]:
        try:
            from platform_reasoning import reasoning_engine
            from platform_reasoning.models import ReasoningContext

            session = await reasoning_engine.reason(ReasoningContext(request=query, metadata=metadata))
            conclusion = getattr(session, "conclusion", None)
            if isinstance(conclusion, dict):
                return conclusion
            return {"analysis": str(conclusion or "completed")}
        except Exception:
            return {"analysis": "fallback"}

    @staticmethod
    async def plan(goal: str, context: dict[str, Any]) -> dict[str, Any]:
        try:
            from applications.auto_marketplace.integrations.platform_bridge import platform_bridge

            return await platform_bridge.plan_purchase_journey(context.get("customer_id", ""), context)
        except Exception:
            return {"steps": ["onboard", "recommend", "qualify", "close"]}

    @staticmethod
    async def decide(request: str, metadata: dict[str, Any]) -> dict[str, Any]:
        try:
            from platform_decision import decision_engine
            from platform_decision.models import DecisionContext

            result = await decision_engine.decide(DecisionContext(request=request, metadata=metadata))
            return {
                "action": getattr(result, "action", "continue"),
                "confidence": getattr(result, "confidence", 0.5),
            }
        except Exception:
            return {"action": "continue", "confidence": 0.5}

    @staticmethod
    async def learn_from_interaction(agent_id: str, rating: float, notes: str) -> None:
        try:
            from applications.auto_marketplace.integrations.platform_bridge import platform_bridge

            await platform_bridge.record_interaction_feedback(agent_id, rating, notes)
        except Exception:
            logger.debug("learning engine unavailable")

    @staticmethod
    async def start_workflow(name: str, steps: list[str], metadata: dict[str, Any]) -> str | None:
        try:
            from platform_workflow import workflow_engine
            from platform_workflow.models import WorkflowStep

            workflow = await workflow_engine.create_workflow(
                name,
                [WorkflowStep(name=s, assignee_id="ai-sales-agent") for s in steps],
                metadata=metadata,
            )
            return workflow.workflow_id
        except Exception:
            return None

    @staticmethod
    async def collaborate(session_key: str, agent_ids: list[str]) -> dict[str, Any]:
        try:
            from applications.auto_marketplace.integrations.platform_bridge import platform_bridge

            return await platform_bridge.collaborate_on_deal(session_key, agent_ids)
        except Exception:
            return {"session_id": session_key, "participants": agent_ids}


ai_sales_platform_bridge = AISalesPlatformBridge()
