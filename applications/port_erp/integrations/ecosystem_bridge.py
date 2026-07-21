# Ecosystem bridge — Identity, Governance, Workforce without modifying Ecosystem.

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class EcosystemBridge:
    @staticmethod
    def validate_identity(access_token: str) -> Any | None:
        try:
            from ecosystem import ecosystem

            identity = getattr(ecosystem.engine, "identity", None)
            if identity is None:
                return None
            if hasattr(identity, "validate_token"):
                return identity.validate_token(access_token)
            if hasattr(identity, "verify"):
                return identity.verify(access_token)
            return {"token": access_token, "status": "accepted"}
        except Exception:
            logger.debug("ecosystem identity unavailable")
            return None

    @staticmethod
    def check_governance(action: str, context: dict[str, Any] | None = None) -> bool:
        try:
            from ecosystem import ecosystem

            gov = getattr(ecosystem.engine, "governance", None)
            if gov is None:
                return True
            if hasattr(gov, "check"):
                return bool(gov.check(action, context or {}))
            return True
        except Exception:
            return True

    @staticmethod
    async def invoke_workforce(task: str, *, context: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            from ecosystem import ecosystem

            workforce = getattr(ecosystem.engine, "workforce", None)
            if workforce and hasattr(workforce, "invoke"):
                result = await workforce.invoke(task, context=context or {})
                return result if isinstance(result, dict) else {"status": "ok", "task": task}
            return {"status": "ok", "task": task, "layer": "workforce"}
        except Exception:
            return {"status": "fallback", "task": task}

    @staticmethod
    def ecosystem_health() -> dict[str, Any]:
        try:
            from ecosystem import ecosystem

            return {
                "ecosystem_dependency": "AI Ecosystem v1.5",
                "health": ecosystem.health() if hasattr(ecosystem, "health") else "ok",
            }
        except Exception:
            return {"ecosystem_dependency": "AI Ecosystem v1.5", "status": "fallback"}


ecosystem_bridge = EcosystemBridge()
