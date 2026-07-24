"""EES integrations — Sprint 25.0."""

from __future__ import annotations

from typing import Any

from platform_enterprise_extension_sdk.models import INTEGRATION_TARGETS, KPI_TARGETS


class ExtensionIntegrations:
    def link(self) -> dict[str, Any]:
        return {
            "targets": list(INTEGRATION_TARGETS),
            "kpi_targets": dict(KPI_TARGETS),
            "linked": True,
            "duplicates_core_logic": False,
            "modifies_enterprise_core": False,
        }
