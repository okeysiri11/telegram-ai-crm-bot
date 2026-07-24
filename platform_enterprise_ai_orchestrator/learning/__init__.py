"""AI Learning — Sprint 24.0."""

from __future__ import annotations

from typing import Any


class AILearning:
    def learn_from_release(
        self,
        *,
        forecast: str,
        actual: str,
        confirmed: bool = False,
        recommendation_adjustment: str = "",
    ) -> dict[str, Any]:
        if not confirmed:
            return {
                "learned": False,
                "reason": "unconfirmed_outcome",
                "requires_confirmed_results": True,
            }
        match = forecast.strip().lower() == actual.strip().lower() if forecast and actual else False
        return {
            "learned": True,
            "forecast": forecast,
            "actual": actual,
            "forecast_matched": match,
            "recommendation_adjustment": recommendation_adjustment
            or ("reinforce" if match else "recalibrate"),
            "confirmed_only": True,
        }
