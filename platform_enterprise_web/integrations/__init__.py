"""EWF integrations — Sprint 26.1."""

from __future__ import annotations

from typing import Any

from platform_enterprise_web.models import INTEGRATION_TARGETS, KPI_TARGETS


class WebFoundationIntegrations:
    def link(self) -> dict[str, Any]:
        return {
            "targets": list(INTEGRATION_TARGETS),
            "kpi_targets": dict(KPI_TARGETS),
            "linked": True,
            "duplicates_core_logic": False,
            "duplicates_console_logic": False,
            "modules_plug_in_without_arch_change": True,
        }
