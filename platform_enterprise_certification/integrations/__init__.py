"""ECF integrations — Sprint 25.7."""

from __future__ import annotations

from typing import Any

from platform_enterprise_certification.models import INTEGRATION_TARGETS, KPI_TARGETS, STAGE_25_COMPLETE


class CertificationIntegrations:
    def link(self) -> dict[str, Any]:
        return {
            "targets": list(INTEGRATION_TARGETS),
            "kpi_targets": dict(KPI_TARGETS),
            "stage_25_complete": list(STAGE_25_COMPLETE),
            "linked": True,
            "duplicates_core_logic": False,
            "duplicates_erl_logic": False,
            "block_release_on_critical": True,
            "ci_cd_required": True,
            "phase3_ready": True,
            "next_phase": "enterprise_web_platform",
            "next_version": "9.0.3",
        }
