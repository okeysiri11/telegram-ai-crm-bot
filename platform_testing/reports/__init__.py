"""Test Reports — Sprint 25.1."""

from __future__ import annotations

from typing import Any

from platform_testing.models import REPORT_FORMATS


class TestReports:
    def generate(self, *, run_id: str, summary: dict[str, Any]) -> dict[str, Any]:
        artifacts = {}
        for fmt in REPORT_FORMATS:
            if fmt == "json":
                artifacts[fmt] = {"run_id": run_id, "summary": summary}
            elif fmt == "xml":
                artifacts[fmt] = f"<report run=\"{run_id}\" passed=\"{summary.get('passed', 0)}\"/>"
            elif fmt == "html":
                artifacts[fmt] = f"<html><body><h1>Run {run_id}</h1><p>passed={summary.get('passed', 0)}</p></body></html>"
            else:
                artifacts[fmt] = f"RUN {run_id} passed={summary.get('passed', 0)} failed={summary.get('failed', 0)}"
        return {
            "run_id": run_id,
            "formats": list(REPORT_FORMATS),
            "artifacts": artifacts,
            "auto_generated": True,
        }
