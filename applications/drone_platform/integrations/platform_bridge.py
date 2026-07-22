# Platform bridge — consumes AI Platform Core via interfaces only (no platform mutations).

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class PlatformBridge:
    """Optional bridge to Platform Core services used by Drone Platform."""

    @staticmethod
    def health() -> dict[str, Any]:
        try:
            # Soft probe — never required for local foundation mode
            import platform_memory  # noqa: F401

            return {"status": "available", "bridge": "platform", "mode": "live"}
        except Exception:
            logger.debug("platform core unavailable; using stub bridge")
            return {"status": "stub", "bridge": "platform", "mode": "offline"}

    @staticmethod
    async def remember_engineering_context(session_id: str, content: str) -> dict[str, Any]:
        try:
            from platform_memory import memory_service

            await memory_service.remember_session_memory(session_id=session_id, content=content)
            return {"status": "stored", "session_id": session_id}
        except Exception:
            return {"status": "stub_stored", "session_id": session_id}


platform_bridge = PlatformBridge()
