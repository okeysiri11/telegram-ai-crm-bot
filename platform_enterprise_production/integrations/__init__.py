"""EPD integrations — Sprint 25.6."""

from __future__ import annotations

from typing import Any

from platform_enterprise_production.models import INTEGRATION_TARGETS, KPI_TARGETS


class ProductionIntegrations:
    def link(self) -> dict[str, Any]:
        return {
            "targets": list(INTEGRATION_TARGETS),
            "kpi_targets": dict(KPI_TARGETS),
            "linked": True,
            "duplicates_core_logic": False,
            "duplicates_obs_logic": False,
            "duplicates_epr_logic": False,
            "block_release_when_not_ready": True,
            "ci_cd_required": True,
        }
