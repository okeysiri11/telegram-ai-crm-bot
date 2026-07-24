"""Business Health Analyzer — Sprint 22.1."""

from __future__ import annotations

from typing import Any

from platform_ai_business_advisor.models import HEALTH_DIMENSIONS, INDUSTRIES


class BusinessHealthAnalyzer:
    BASELINES = {
        "sales": 1.0,
        "profit": 0.92,
        "expenses": 0.88,
        "customers": 0.95,
        "repeat_visits": 0.78,
        "staff_efficiency": 0.81,
        "schedule_load": 0.74,
        "service_usage": 0.83,
        "marketing_campaigns": 0.69,
    }

    def analyze(self, *, industry: str = "generic", snapshot: dict[str, float] | None = None) -> dict[str, Any]:
        if industry not in INDUSTRIES:
            raise ValueError(f"unsupported industry: {industry}")
        metrics = dict(self.BASELINES)
        if snapshot:
            metrics.update({k: float(v) for k, v in snapshot.items() if k in HEALTH_DIMENSIONS})
        scores = [{"dimension": d, "score": metrics[d], "healthy": metrics[d] >= 0.75} for d in HEALTH_DIMENSIONS]
        overall = sum(m["score"] for m in scores) / len(scores)
        return {
            "industry": industry,
            "scores": scores,
            "overall": round(overall, 3),
            "problems": [s["dimension"] for s in scores if not s["healthy"]],
            "passed": True,
        }
