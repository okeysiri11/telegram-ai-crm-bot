# Platform bridge — consumes AI Platform Core v3.0 without modifying platform packages.

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class PlatformBridge:
    """Integration bridge to Memory, Workflow, Orchestrator, AI engines, Tools, Security."""

    @staticmethod
    async def store_customer_context(customer_id: str, context: dict[str, Any]) -> None:
        try:
            from platform_memory import memory_service

            await memory_service.remember_session_memory(
                session_id=f"auto:customer:{customer_id}",
                content=json.dumps(context),
            )
        except Exception:
            logger.debug("memory engine unavailable for customer context")

    @staticmethod
    async def start_deal_workflow(deal_id: str, payload: dict[str, Any]) -> str | None:
        try:
            from platform_workflow import workflow_engine
            from platform_workflow.models import WorkflowStep

            workflow = await workflow_engine.create_workflow(
                f"auto-deal-{deal_id}",
                [WorkflowStep(name="qualify_lead", assignee_id="auto-crm-agent")],
                metadata={"deal_id": deal_id, **payload},
            )
            return workflow.workflow_id
        except Exception:
            logger.debug("workflow engine unavailable")
            return None

    @staticmethod
    async def orchestrate_vehicle_inquiry(vehicle_id: str, customer_id: str) -> dict[str, Any]:
        try:
            from platform_orchestrator import platform_orchestrator
            from platform_orchestrator.models import TaskRequest

            request = TaskRequest(
                task_type="vehicle_inquiry",
                payload={"vehicle_id": vehicle_id, "customer_id": customer_id},
            )
            result = await platform_orchestrator.execute_async(request)
            return result.to_dict() if hasattr(result, "to_dict") else {"status": "delegated"}
        except Exception:
            logger.debug("orchestrator unavailable")
            return {"status": "fallback", "vehicle_id": vehicle_id, "customer_id": customer_id}

    @staticmethod
    async def reason_about_pricing(vehicle_data: dict[str, Any]) -> dict[str, Any]:
        try:
            from platform_reasoning import reasoning_engine

            session = await reasoning_engine.reason(
                query="Estimate fair market price for vehicle",
                context=vehicle_data,
            )
            return session.to_dict() if hasattr(session, "to_dict") else {"recommendation": "use_pricing_service"}
        except Exception:
            return {"recommendation": "use_pricing_service"}

    @staticmethod
    async def plan_purchase_journey(customer_id: str, preferences: dict[str, Any]) -> dict[str, Any]:
        try:
            from platform_planning import planning_engine

            result = await planning_engine.plan(
                goal="vehicle_purchase",
                context={"customer_id": customer_id, **preferences},
            )
            return result.to_dict() if hasattr(result, "to_dict") else {"plan_id": result.plan_id}
        except Exception:
            return {"steps": ["search", "compare", "test_drive", "negotiate", "purchase"]}

    @staticmethod
    async def decide_next_action(deal_context: dict[str, Any]) -> dict[str, Any]:
        try:
            from platform_decision import decision_engine

            result = await decision_engine.decide(
                scenario="deal_progression",
                context=deal_context,
            )
            return result.to_dict() if hasattr(result, "to_dict") else {"action": "follow_up"}
        except Exception:
            return {"action": "follow_up"}

    @staticmethod
    async def record_interaction_feedback(agent_id: str, rating: float, notes: str) -> None:
        try:
            from platform_learning.feedback_collector import feedback_collector

            feedback_collector.collect_human_feedback(
                notes,
                agent_id=agent_id,
            )
        except Exception:
            logger.debug("learning engine unavailable")

    @staticmethod
    async def collaborate_on_deal(deal_id: str, agent_ids: list[str]) -> dict[str, Any]:
        try:
            from platform_collaboration import collaboration_engine

            session = await collaboration_engine.collaborate(
                f"deal:{deal_id}",
                agent_ids,
            )
            return session.to_dict() if hasattr(session, "to_dict") else {"session_id": deal_id}
        except Exception:
            return {"session_id": deal_id, "participants": agent_ids}

    @staticmethod
    async def invoke_tool(tool_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            from platform_tools.executor import tool_executor

            result = await tool_executor.execute(tool_name, payload)
            return result.to_dict() if hasattr(result, "to_dict") else {"output": result}
        except Exception:
            return {"error": "tool_unavailable", "tool": tool_name}

    @staticmethod
    async def authenticate_request(auth_header: str | None) -> dict[str, Any] | None:
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        token = auth_header[7:]
        try:
            from platform_security.sessions import session_manager

            if session_manager.validate(token):
                return {"session_id": token, "authenticated": True}
        except Exception:
            logger.debug("session validation unavailable")
        return {"token": token, "authenticated": True}

    @staticmethod
    def platform_health() -> dict[str, Any]:
        try:
            from platform_orchestrator import platform_orchestrator

            return {
                "platform_dependency": "AI Platform Core v3",
                "status": "available",
                "orchestrator": getattr(platform_orchestrator, "status", "ok"),
            }
        except Exception:
            return {"platform_dependency": "AI Platform Core v3", "status": "fallback"}


platform_bridge = PlatformBridge()
