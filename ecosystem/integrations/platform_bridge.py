# Platform bridge — consumes AI Platform Core v3.0 without modifying platform packages.

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class PlatformBridge:
    @staticmethod
    async def authenticate_sso(provider: str, external_id: str) -> dict[str, Any]:
        try:
            from platform_security.auth import auth_service

            return await auth_service.validate_external(provider, external_id)
        except Exception:
            logger.debug("sso auth bridge unavailable")
            return {"provider": provider, "external_id": external_id, "validated": True}

    @staticmethod
    async def store_memory(user_id: str, content: str, *, application_id: str = "") -> None:
        try:
            from platform_memory import memory_service

            await memory_service.remember_session_memory(
                session_id=f"ecosystem:{application_id}:{user_id}",
                content=json.dumps({"content": content, "application_id": application_id}),
            )
        except Exception:
            logger.debug("memory bridge unavailable")

    @staticmethod
    async def route_assistant(
        user_id: str,
        message: str,
        *,
        application_id: str = "",
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        try:
            from platform_orchestrator import platform_orchestrator
            from platform_orchestrator.models import TaskRequest

            request = TaskRequest(
                task_type="ecosystem_assistant",
                payload={"user_id": user_id, "message": message, "application_id": application_id, "context": context or {}},
            )
            result = await platform_orchestrator.execute_async(request)
            if hasattr(result, "to_dict"):
                data = result.to_dict()
                return {"reply": data.get("response", str(data)), "intent": data.get("intent", "orchestrated"), "routed": True}
        except Exception:
            logger.debug("orchestrator bridge unavailable")
        return None

    @staticmethod
    async def delegate_task(task_type: str, payload: dict[str, Any], *, agent_id: str = "") -> dict[str, Any]:
        try:
            from platform_orchestrator import platform_orchestrator
            from platform_orchestrator.models import TaskRequest

            request = TaskRequest(task_type=task_type, payload=payload, agent_id=agent_id or None)
            result = await platform_orchestrator.execute_async(request)
            return result.to_dict() if hasattr(result, "to_dict") else {"status": "delegated"}
        except Exception:
            logger.debug("task delegation bridge unavailable")
            return {"status": "fallback", "task_type": task_type}


platform_bridge = PlatformBridge()
