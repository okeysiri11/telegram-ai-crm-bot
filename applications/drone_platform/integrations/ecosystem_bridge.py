# Ecosystem bridge — optional identity/tenant hooks without modifying ecosystem packages.

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class EcosystemBridge:
    @staticmethod
    def health() -> dict[str, Any]:
        try:
            import ecosystem  # noqa: F401

            return {"status": "available", "bridge": "ecosystem", "mode": "live"}
        except Exception:
            logger.debug("ecosystem unavailable; using stub bridge")
            return {"status": "stub", "bridge": "ecosystem", "mode": "offline"}

    @staticmethod
    def resolve_tenant_context(tenant_id: str) -> dict[str, Any]:
        try:
            from ecosystem.tenants.service import tenant_service

            tenant = tenant_service.get_tenant(tenant_id)
            return {"status": "ok", "tenant": getattr(tenant, "to_dict", lambda: {"tenant_id": tenant_id})()}
        except Exception:
            return {"status": "stub", "tenant_id": tenant_id}


ecosystem_bridge = EcosystemBridge()
