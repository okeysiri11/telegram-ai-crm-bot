"""Client Portal integrations — Sprint 22.8."""

from __future__ import annotations

from typing import Any

from platform_client_portal.models import INTEGRATION_TARGETS, KPI_TARGETS


class PortalIntegrations:
    def link(self) -> dict[str, Any]:
        return {
            "targets": list(INTEGRATION_TARGETS),
            "kpi_targets": dict(KPI_TARGETS),
            "linked": True,
            "duplicates_core_logic": False,
        }
