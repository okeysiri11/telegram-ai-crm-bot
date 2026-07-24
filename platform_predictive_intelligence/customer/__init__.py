"""Customer Prediction Engine — Sprint 24.3."""

from __future__ import annotations

from typing import Any

from platform_predictive_intelligence.models import CUSTOMER_PREDICTIONS


class CustomerPredictionEngine:
    def predict(self, *, customer_id: str, signals: dict[str, Any] | None = None) -> dict[str, Any]:
        if not customer_id:
            raise ValueError("customer_id is required")
        signals = dict(signals or {})
        days = float(signals.get("days_since_visit", 30))
        visits = float(signals.get("visits", 5))
        spend = float(signals.get("spend", 200))
        revisit = max(0.05, min(0.95, 0.9 - days / 200))
        churn = max(0.05, min(0.95, days / 120))
        purchase = max(0.05, min(0.95, 0.4 + visits / 20))
        ltv = round(spend * (1 + revisit), 2)
        return {
            "customer_id": customer_id,
            "revisit_probability": round(revisit, 3),
            "churn_probability": round(churn, 3),
            "purchase_probability": round(purchase, 3),
            "expected_ltv": ltv,
            "promo_sensitivity": round(min(0.95, 0.3 + churn * 0.4), 3),
            "loyalty_level": "high" if visits >= 8 else ("medium" if visits >= 3 else "low"),
            "metrics": list(CUSTOMER_PREDICTIONS),
        }
