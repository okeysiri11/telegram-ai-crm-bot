"""Long-Term Forecast — Sprint 24.7."""

from __future__ import annotations

from typing import Any

from platform_enterprise_strategy_intelligence.models import FORECAST_HORIZONS


class LongTermForecast:
    SOURCES = ("predictive_intelligence", "enterprise_digital_twin", "simulation_lab", "enterprise_knowledge_graph")

    def project(self, *, baseline: float, growth_rate: float = 0.1, horizon: str = "year") -> dict[str, Any]:
        horizon = (horizon or "year").lower()
        if horizon not in FORECAST_HORIZONS:
            raise ValueError(f"unsupported horizon: {horizon}")
        multipliers = {
            "quarter": 0.25,
            "half_year": 0.5,
            "year": 1.0,
            "three_years": 3.0,
            "five_years": 5.0,
        }
        years = multipliers[horizon]
        projected = float(baseline) * ((1.0 + float(growth_rate)) ** years)
        return {
            "horizon": horizon,
            "baseline": float(baseline),
            "growth_rate": float(growth_rate),
            "projected": round(projected, 2),
            "sources": list(self.SOURCES),
            "horizons": list(FORECAST_HORIZONS),
        }
