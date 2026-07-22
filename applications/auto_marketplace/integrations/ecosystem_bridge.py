# Ecosystem bridge — Identity / Governance / Workforce without modifying Ecosystem.

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class EcosystemBridge:
    """Bridge to AI Ecosystem v1.5 — Auto Marketplace only."""

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
    def ecosystem_health() -> dict[str, Any]:
        try:
            from ecosystem import ecosystem

            return {
                "ecosystem_dependency": "AI Ecosystem v1.5",
                "health": ecosystem.health() if hasattr(ecosystem, "health") else "ok",
                "status": "available",
            }
        except Exception:
            return {"ecosystem_dependency": "AI Ecosystem v1.5", "status": "fallback"}


ecosystem_bridge = EcosystemBridge()
