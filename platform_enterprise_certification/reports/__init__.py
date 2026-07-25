"""Release Reports — Sprint 25.7."""

from __future__ import annotations

from typing import Any

from platform_enterprise_certification.models import REPORT_KINDS


class ReleaseReports:
    def generate(self, *, run_id: str, summary: dict[str, Any]) -> dict[str, Any]:
        reports = {kind: {"run_id": run_id, "kind": kind, "summary": summary} for kind in REPORT_KINDS}
        return {
            "reports": reports,
            "kinds": list(REPORT_KINDS),
            "unified_certification_report": True,
            "auto_generated": True,
        }
