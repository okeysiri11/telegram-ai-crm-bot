"""Communications Hub integrations — Sprint 22.6."""

from __future__ import annotations

from typing import Any

from platform_communications_hub.models import INDUSTRIES, INTEGRATION_TARGETS


class HubIntegrations:
    def link(self) -> dict[str, Any]:
        return {
            "targets": list(INTEGRATION_TARGETS),
            "industries": list(INDUSTRIES),
            "linked": True,
            "duplicates_core_logic": False,
            "universal_api": True,
            "existing_comms_ref": "enterprise_comms",
        }
