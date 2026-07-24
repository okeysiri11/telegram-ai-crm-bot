"""Forecast Engine — Sprint 22.1."""

from __future__ import annotations

from typing import Any

from platform_ai_business_advisor.models import FORECAST_KINDS


class ForecastEngine:
    def forecast(self, health: dict[str, Any], horizon_days: int = 30) -> dict[str, Any]:
        overall = float(health.get("overall") or 0.8)
        base = {
            "revenue": round(100000 * overall, 2),
            "profit": round(28000 * overall, 2),
            "staff_load": round(0.7 * overall, 3),
            "bookings": int(420 * overall),
            "demand": round(0.85 * overall, 3),
        }
        forecasts = [{"kind": k, "value": base[k], "horizon_days": horizon_days} for k in FORECAST_KINDS]
        return {"forecasts": forecasts, "horizon_days": horizon_days, "passed": True}
