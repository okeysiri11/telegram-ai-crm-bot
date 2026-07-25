"""EDS integrations — Sprint 26.2."""

from __future__ import annotations

from typing import Any

from platform_enterprise_design_system.models import INTEGRATION_TARGETS, KPI_TARGETS


class DesignSystemIntegrations:
    def link(self) -> dict[str, Any]:
        return {
            "targets": list(INTEGRATION_TARGETS),
            "kpi_targets": dict(KPI_TARGETS),
            "linked": True,
            "duplicates_ui_standards": False,
            "web_modules_use_single_ds": True,
        }
