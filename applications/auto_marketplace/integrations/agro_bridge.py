# Agro Marketplace bridge — consume only, never modify Agro packages.

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class AgroMarketplaceBridge:
    """Native bridge to Agro Marketplace without modifying applications/agro_marketplace."""

    TARGET = "agro_marketplace"

    def health(self) -> dict[str, Any]:
        try:
            from applications.agro_marketplace import agro_marketplace  # type: ignore

            h = agro_marketplace.health() if hasattr(agro_marketplace, "health") else {}
            return {"target": self.TARGET, "status": "reachable", "version": h.get("application_version", "unknown")}
        except Exception:
            logger.debug("agro marketplace unavailable")
            return {"target": self.TARGET, "status": "unavailable", "mode": "stub"}

    def share_identity(self, user_id: str) -> dict[str, Any]:
        return {"shared": "identity", "user_id": user_id, "with": self.TARGET, "status": "queued"}

    def share_analytics(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"shared": "analytics", "with": self.TARGET, "keys": list(payload.keys()), "status": "queued"}


agro_marketplace_bridge = AgroMarketplaceBridge()
