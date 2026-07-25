"""Security Reports — Sprint 25.5."""

from __future__ import annotations

from typing import Any

from platform_enterprise_security_verification.models import REPORT_KINDS


class SecurityReports:
    def generate(self, *, run_id: str, summary: dict[str, Any]) -> dict[str, Any]:
        artifacts = {kind: {"run_id": run_id, "kind": kind, "summary": summary} for kind in REPORT_KINDS}
        return {
            "run_id": run_id,
            "kinds": list(REPORT_KINDS),
            "artifacts": artifacts,
            "auto_generated": True,
            "unified_security_report": True,
        }
