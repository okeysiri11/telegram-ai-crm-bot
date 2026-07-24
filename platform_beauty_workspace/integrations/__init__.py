"""Beauty Workspace integrations — Sprint 22.3."""

from __future__ import annotations

from typing import Any

from platform_beauty_workspace.models import INTEGRATION_TARGETS


class WorkspaceIntegrations:
    def link(self) -> dict[str, Any]:
        return {
            "targets": list(INTEGRATION_TARGETS),
            "linked": True,
            "duplicates_core_logic": False,
            "beauty_os": "beauty_os",
            "crm": "enterprise_crm",
            "calendar": "enterprise_calendar",
            "ai_business_advisor": "ai_business_advisor",
            "product_intelligence": "product_intelligence",
            "notification_center": "beauty_workspace.notifications",
        }
