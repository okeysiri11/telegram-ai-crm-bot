"""Risk Simulator — Sprint 24.4."""

from __future__ import annotations

from typing import Any


class RiskSimulator:
    def assess(self, *, impact_risks: float = 0.2, intensity: float = 1.0) -> dict[str, Any]:
        impact_risks = max(0.0, min(1.0, float(impact_risks) * float(intensity)))
        return {
            "failure_probability": round(min(0.95, 0.1 + impact_risks), 3),
            "financial_loss": round(impact_risks * 1000, 2),
            "customer_impact": round(impact_risks * 0.8, 3),
            "employee_impact": round(impact_risks * 0.5, 3),
            "critical_points": ["cashflow", "staff_load"] if impact_risks >= 0.3 else ["monitoring"],
        }
