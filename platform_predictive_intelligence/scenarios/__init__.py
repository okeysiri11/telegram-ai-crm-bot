"""AI Scenario Generator — Sprint 24.3."""

from __future__ import annotations

from typing import Any

from platform_predictive_intelligence.models import SCENARIO_KINDS


class AIScenarioGenerator:
    def generate(self, *, baseline: float, domain: str = "revenue") -> dict[str, Any]:
        baseline = float(baseline)
        scenarios = {
            "optimistic": round(baseline * 1.15, 2),
            "baseline": round(baseline, 2),
            "conservative": round(baseline * 0.9, 2),
            "crisis": round(baseline * 0.7, 2),
        }
        return {"domain": domain, "scenarios": scenarios, "kinds": list(SCENARIO_KINDS)}
