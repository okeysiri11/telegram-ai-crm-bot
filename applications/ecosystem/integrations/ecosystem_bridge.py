"""Ecosystem bridge — consume top-level AI Ecosystem v1.5 without modifying it (Sprint 12.0)."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class EcosystemBridge:
    @staticmethod
    def health() -> dict[str, Any]:
        try:
            from ecosystem import ecosystem

            return {
                "ecosystem_dependency": "AI Ecosystem v1.5",
                "health": ecosystem.health() if hasattr(ecosystem, "health") else {"status": "ok"},
                "modified": False,
            }
        except Exception:
            logger.debug("top-level ecosystem unavailable")
            return {"ecosystem_dependency": "AI Ecosystem v1.5", "status": "fallback", "modified": False}


ecosystem_bridge = EcosystemBridge()
