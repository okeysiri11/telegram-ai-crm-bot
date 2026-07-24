"""Business Forecast Engine — Sprint 24.3."""

from __future__ import annotations

from typing import Any

from platform_predictive_intelligence.models import FORECAST_DOMAINS


class BusinessForecastEngine:
    def forecast(self, *, domain: str, horizon_days: int = 30, baseline: float = 100.0) -> dict[str, Any]:
        domain = (domain or "").lower()
        if domain not in FORECAST_DOMAINS:
            raise ValueError(f"unsupported domain: {domain}")
        baseline = float(baseline)
        horizon_days = max(1, int(horizon_days))
        growth = 0.02 * (horizon_days / 30)
        return {
            "domain": domain,
            "horizon_days": horizon_days,
            "baseline": baseline,
            "forecast_value": round(baseline * (1 + growth), 2),
            "unit": "currency" if domain in ("revenue", "profit", "sales", "expenses", "cashflow") else "index",
        }
