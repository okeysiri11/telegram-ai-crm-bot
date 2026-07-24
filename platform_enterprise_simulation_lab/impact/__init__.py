"""AI Impact Analyzer — Sprint 24.4."""

from __future__ import annotations

from typing import Any

from platform_enterprise_simulation_lab.models import IMPACT_DIMS


class AIImpactAnalyzer:
    def analyze(self, *, deltas: dict[str, float] | None = None) -> dict[str, Any]:
        deltas = dict(deltas or {})
        impact = {}
        mapping = {
            "finance": "profit",
            "sales": "revenue",
            "workforce": "staff_load",
            "marketing": "marketing",
            "inventory": "inventory",
            "branch_load": "staff_load",
        }
        for dim in IMPACT_DIMS:
            impact[dim] = 0.0
        for domain, delta in deltas.items():
            target = mapping.get(domain)
            if target:
                impact[target] = round(impact.get(target, 0.0) + float(delta), 4)
        # derived
        impact["cashflow"] = round(impact.get("profit", 0) * 0.8 + impact.get("revenue", 0) * 0.2, 4)
        impact["customer_satisfaction"] = round(-abs(impact.get("staff_load", 0)) * 0.3 + impact.get("revenue", 0) * 0.2, 4)
        impact["risks"] = round(max(0.0, -impact.get("profit", 0) * 0.5 + abs(impact.get("staff_load", 0)) * 0.4), 4)
        return {"impacts": impact, "dimensions": list(IMPACT_DIMS), "explained": True}
