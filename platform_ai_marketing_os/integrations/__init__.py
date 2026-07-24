"""Marketing OS integrations — Sprint 22.5."""

from __future__ import annotations

from typing import Any

from platform_ai_marketing_os.models import INTEGRATION_TARGETS


class MarketingIntegrations:
    def link(self) -> dict[str, Any]:
        return {
            "targets": list(INTEGRATION_TARGETS),
            "linked": True,
            "duplicates_core_logic": False,
            "edition": "beauty",
        }
