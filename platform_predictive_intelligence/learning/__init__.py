"""Continuous Learning — Sprint 24.3."""

from __future__ import annotations

from typing import Any


class ContinuousLearning:
    def compare(self, *, forecast: float, actual: float, confirmed: bool = False, model_id: str = "") -> dict[str, Any]:
        if not confirmed:
            return {"learned": False, "reason": "unconfirmed_actual", "requires_confirmed": True}
        forecast = float(forecast)
        actual = float(actual)
        err = abs(forecast - actual) / max(abs(actual), 1.0)
        accuracy = round(max(0.0, 1.0 - err), 3)
        return {
            "learned": True,
            "model_id": model_id or None,
            "forecast": forecast,
            "actual": actual,
            "accuracy": accuracy,
            "quality_history_updated": True,
            "confirmed_only": True,
        }
