"""APH integrations — Sprint 24.9."""

from __future__ import annotations

from typing import Any

from platform_enterprise_ai_provider_hub.models import INTEGRATION_TARGETS, KPI_TARGETS


class ProviderHubIntegrations:
    def link(self) -> dict[str, Any]:
        return {
            "targets": list(INTEGRATION_TARGETS),
            "kpi_targets": dict(KPI_TARGETS),
            "linked": True,
            "duplicates_core_logic": False,
            "business_modules_call_hub_only": True,
        }
