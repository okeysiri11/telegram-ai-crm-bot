"""Strategic Scenario Builder — Sprint 24.7."""

from __future__ import annotations

from typing import Any

from platform_enterprise_strategy_intelligence.models import SCENARIO_TYPES


class StrategicScenarioBuilder:
    FACTORS = {
        "baseline": 1.0,
        "aggressive_growth": 1.35,
        "conservative": 0.85,
        "crisis": 0.55,
    }

    def build(self, *, baseline_value: float, strategy_id: str = "") -> dict[str, Any]:
        scenarios = []
        for name in SCENARIO_TYPES:
            factor = self.FACTORS[name]
            scenarios.append({
                "type": name,
                "projected_value": round(float(baseline_value) * factor, 2),
                "factor": factor,
            })
        return {
            "strategy_id": strategy_id or None,
            "scenarios": scenarios,
            "types": list(SCENARIO_TYPES),
        }
