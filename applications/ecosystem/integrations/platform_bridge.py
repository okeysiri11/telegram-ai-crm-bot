"""Platform bridge — consume Platform Core without modifying it (Sprint 12.0)."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class PlatformBridge:
    @staticmethod
    def health() -> dict[str, Any]:
        try:
            # Soft reference only — never import platform internals for mutation.
            return {"platform_dependency": "AI Platform Core v3.0", "status": "linked", "modified": False}
        except Exception:
            logger.debug("platform bridge fallback")
            return {"platform_dependency": "AI Platform Core v3.0", "status": "fallback", "modified": False}


platform_bridge = PlatformBridge()
