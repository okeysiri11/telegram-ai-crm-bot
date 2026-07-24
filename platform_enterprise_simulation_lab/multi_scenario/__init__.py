"""Multi-Scenario Engine — Sprint 24.4."""

from __future__ import annotations

from typing import Any

from platform_enterprise_simulation_lab.models import SCENARIO_KINDS


class MultiScenarioEngine:
    def expand(self, *, baseline: float, domain: str = "finance") -> dict[str, Any]:
        baseline = float(baseline)
        scenarios = {
            "optimistic": round(baseline * 1.2, 2),
            "realistic": round(baseline, 2),
            "conservative": round(baseline * 0.9, 2),
            "crisis": round(baseline * 0.65, 2),
        }
        return {"domain": domain, "scenarios": scenarios, "kinds": list(SCENARIO_KINDS)}
