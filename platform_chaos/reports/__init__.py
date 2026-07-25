"""Chaos Reports — Sprint 25.3."""

from __future__ import annotations

from typing import Any

from platform_chaos.models import REPORT_FORMATS


class ChaosReports:
    def generate(self, *, run_id: str, summary: dict[str, Any]) -> dict[str, Any]:
        artifacts = {
            "html": f"<html><body><h1>Chaos {run_id}</h1></body></html>",
            "json": {"run_id": run_id, "summary": summary},
            "incident_timeline": summary.get("incidents", []),
            "recovery_timeline": summary.get("recovery_events", []),
            "root_cause": summary.get("root_cause", "injected_failure"),
            "recommendations": summary.get("recommendations", []),
        }
        return {
            "run_id": run_id,
            "formats": list(REPORT_FORMATS),
            "artifacts": artifacts,
            "auto_generated": True,
        }
