"""Commerce integrations — Sprint 22.7."""

from __future__ import annotations

from typing import Any

from platform_enterprise_commerce.models import INDUSTRIES, INTEGRATION_TARGETS, KPI_TARGETS


class CommerceIntegrations:
    def link(self) -> dict[str, Any]:
        return {
            "targets": list(INTEGRATION_TARGETS),
            "industries": list(INDUSTRIES),
            "kpi_targets": dict(KPI_TARGETS),
            "linked": True,
            "duplicates_core_logic": False,
            "universal": True,
        }
