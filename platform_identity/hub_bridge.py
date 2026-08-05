"""Hub ISAM → Platform Identity adapter bridge — Sprint 35.1.

Does not rewrite Hub auth. Registers ISAM as a consumer of canonical Identity Core.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class HubIdentityBridge:
    """Thin bridge: Hub/ISAM principals resolve through platform_identity."""

    @staticmethod
    async def resolve_telegram(telegram_id: int) -> dict[str, Any] | None:
        try:
            from platform_identity.identity_service import identity_service

            principal = await identity_service.authenticate_telegram(telegram_id)
            return {
                "principal_id": getattr(principal, "principal_id", None),
                "telegram_id": getattr(principal, "telegram_id", telegram_id),
                "roles": list(getattr(principal, "roles", []) or []),
                "permissions": sorted(getattr(principal, "permissions", []) or []),
                "adapter": "hub_isam",
                "canonical": "platform_identity",
            }
        except Exception as exc:  # noqa: BLE001
            logger.debug("HubIdentityBridge resolve failed: %s", exc)
            return None

    @staticmethod
    def status() -> dict[str, Any]:
        return {
            "adapter": "applications/enterprise_hub/security",
            "canonical": "platform_identity",
            "mode": "bridge_only",
            "sprint": "35.1",
            "rewrites_hub_auth": False,
        }


hub_identity_bridge = HubIdentityBridge()
