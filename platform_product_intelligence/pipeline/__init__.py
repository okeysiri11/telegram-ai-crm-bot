"""Development pipeline — Sprint 22.0."""

from __future__ import annotations

from typing import Any

from platform_product_intelligence.models import PIPELINE_ARTIFACTS


class DevelopmentPipeline:
    def create(self, *, report: dict[str, Any], approval: dict[str, Any]) -> dict[str, Any]:
        if not approval.get("development_allowed"):
            raise ValueError("development pipeline requires owner approval")
        title = report.get("proposed_solution") or report.get("problem") or "initiative"
        artifacts = []
        for kind in PIPELINE_ARTIFACTS:
            artifacts.append(
                {
                    "kind": kind,
                    "title": f"{kind}: {title}"[:120],
                    "priority": report.get("priority", "P2"),
                    "kpi": report.get("kpi", []),
                }
            )
        return {
            "artifacts": artifacts,
            "count": len(artifacts),
            "owner_id": approval.get("owner_id"),
            "status": "queued",
            "passed": True,
        }
