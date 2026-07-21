# Platform bridge — consumes AI Platform Core without modifying platform packages.

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class PlatformBridge:
    """Bridge to Memory, Workflow, Orchestrator, Event Bus — Port ERP only."""

    @staticmethod
    async def remember_context(session_key: str, context: dict[str, Any]) -> None:
        try:
            from platform_memory import memory_service

            await memory_service.remember_session_memory(
                session_id=f"port:{session_key}",
                content=json.dumps(context),
            )
        except Exception:
            logger.debug("memory engine unavailable for port context")

    @staticmethod
    async def start_port_workflow(name: str, payload: dict[str, Any]) -> str | None:
        try:
            from platform_workflow import workflow_engine
            from platform_workflow.models import WorkflowStep

            workflow = await workflow_engine.create_workflow(
                f"port-{name}",
                [
                    WorkflowStep(name="plan", assignee_id="port-ops-agent"),
                    WorkflowStep(name="execute", assignee_id="port-ops-agent"),
                ],
                metadata={"application": "port_erp", **payload},
            )
            return workflow.workflow_id
        except Exception:
            logger.debug("workflow engine unavailable")
            return None

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
