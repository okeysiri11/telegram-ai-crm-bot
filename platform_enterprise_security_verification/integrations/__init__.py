"""ESV integrations — Sprint 25.5."""

from __future__ import annotations

from typing import Any

from platform_enterprise_security_verification.models import INTEGRATION_TARGETS, KPI_TARGETS


class SecurityVerificationIntegrations:
    def link(self) -> dict[str, Any]:
        return {
            "targets": list(INTEGRATION_TARGETS),
            "kpi_targets": dict(KPI_TARGETS),
            "linked": True,
            "duplicates_core_logic": False,
            "duplicates_esh_logic": False,
            "block_release_on_critical": True,
        }
