"""Readiness Analyzer — Sprint 25.7."""

from __future__ import annotations

from typing import Any

from platform_enterprise_certification.models import READINESS_DIMENSIONS


class ReadinessAnalyzer:
    def analyze(self, *, scores: dict[str, float] | None = None) -> dict[str, Any]:
        defaults = {d: 100.0 for d in READINESS_DIMENSIONS}
        if scores:
            defaults.update({k: float(v) for k, v in scores.items() if k in defaults})
        dimensions = [{"dimension": d, "score": defaults[d]} for d in READINESS_DIMENSIONS]
        overall = sum(x["score"] for x in dimensions) / len(dimensions)
        return {
            "dimensions": dimensions,
            "overall_readiness_percent": round(overall, 2),
            "passed": overall >= 95.0,
            "enterprise_ready": overall >= 95.0,
        }
