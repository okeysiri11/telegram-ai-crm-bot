# Platform bridge — consumes AI Platform Core v3.0 without modifying platform packages.

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class PlatformBridge:
    """Bridge to Memory, Workflow, Orchestrator, Reasoning, Tools, Security, Event Bus."""

    @staticmethod
    async def store_farmer_context(farmer_id: str, context: dict[str, Any]) -> None:
        try:
            from platform_memory import memory_service

            await memory_service.remember_session_memory(
                session_id=f"agro:farmer:{farmer_id}",
                content=json.dumps(context),
            )
        except Exception:
            logger.debug("memory engine unavailable for farmer context")

    @staticmethod
    async def start_order_workflow(order_id: str, payload: dict[str, Any]) -> str | None:
        try:
            from platform_workflow import workflow_engine
            from platform_workflow.models import WorkflowStep

            workflow = await workflow_engine.create_workflow(
                f"agro-order-{order_id}",
                [
                    WorkflowStep(name="confirm_order", assignee_id="agro-order-agent"),
                    WorkflowStep(name="fulfill", assignee_id="agro-logistics-agent"),
                ],
                metadata={"order_id": order_id, **payload},
            )
            return workflow.workflow_id
        except Exception:
            logger.debug("workflow engine unavailable")
            return None

    @staticmethod
    async def recommend_products(context: dict[str, Any]) -> dict[str, Any]:
        try:
            from platform_reasoning import reasoning_engine

            session = await reasoning_engine.reason(
                query="Recommend agricultural products for buyer",
                context=context,
            )
            return session.to_dict() if hasattr(session, "to_dict") else {"status": "ok"}
        except Exception:
            return {"status": "fallback", "recommendations": []}

    @staticmethod
    async def orchestrate_export(shipment_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            from platform_orchestrator import platform_orchestrator
            from platform_orchestrator.models import TaskRequest

            request = TaskRequest(
                task_type="agro_export",
                payload={"shipment_id": shipment_id, **payload},
            )
            result = await platform_orchestrator.execute_async(request)
            return result.to_dict() if hasattr(result, "to_dict") else {"status": "delegated"}
        except Exception:
            return {"status": "fallback", "shipment_id": shipment_id}

    @staticmethod
    async def remember_context(session_key: str, context: dict[str, Any]) -> None:
        try:
            from platform_memory import memory_service

            await memory_service.remember_session_memory(
                session_id=f"agro:ai:{session_key}",
                content=json.dumps(context),
            )
        except Exception:
            logger.debug("memory engine unavailable for AI context")

    @staticmethod
    async def start_ai_workflow(name: str, payload: dict[str, Any]) -> str | None:
        try:
            from platform_workflow import workflow_engine
            from platform_workflow.models import WorkflowStep

            workflow = await workflow_engine.create_workflow(
                f"agro-ai-{name}",
                [
                    WorkflowStep(name="analyze", assignee_id="agro-ai-agent"),
                    WorkflowStep(name="act", assignee_id="agro-ai-agent"),
                ],
                metadata={"application": "agro_marketplace", **payload},
            )
            return workflow.workflow_id
        except Exception:
            logger.debug("AI workflow unavailable")
            return None

    @staticmethod
    def platform_health() -> dict[str, Any]:
        return {
            "platform_dependency": "AI Platform Core v3.0",
            "bridges": [
                "memory",
                "workflow",
                "orchestrator",
                "reasoning",
                "event_bus",
            ],
        }


platform_bridge = PlatformBridge()
