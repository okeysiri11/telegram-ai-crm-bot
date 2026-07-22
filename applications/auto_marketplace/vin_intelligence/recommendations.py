"""AI recommendations & scoring — Sprint 13.1."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AIRecommendations:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store

    def score(
        self,
        *,
        vin: str,
        fraud_score: float = 0.0,
        accident_prob: float = 0.2,
        market_value: float = 20000.0,
        mileage: int = 50000,
    ) -> dict[str, Any]:
        vin = (vin or "").strip().upper()
        purchase = max(0.0, min(100.0, 88 - fraud_score * 40 - accident_prob * 30 - mileage / 5000))
        risk = max(0.0, min(100.0, fraud_score * 50 + accident_prob * 40 + (10 if mileage > 120000 else 0)))
        investment = max(0.0, min(100.0, purchase * 0.7 + (market_value / 500)))
        dealer = max(0.0, min(100.0, 75 - fraud_score * 25))
        insurance = max(0.0, min(100.0, 70 - accident_prob * 50))
        ownership_cost = round(1800 + mileage * 0.04 + accident_prob * 800, 2)
        rid = _id("virec")
        result = {
            "recommendation_id": rid,
            "vin": vin,
            "purchase_score": round(purchase, 1),
            "risk_score": round(risk, 1),
            "investment_score": round(investment, 1),
            "dealer_score": round(dealer, 1),
            "insurance_score": round(insurance, 1),
            "maintenance_plan": [
                {"interval_miles": 10000, "tasks": ["oil_change", "inspection"]},
                {"interval_miles": 40000, "tasks": ["fluids", "brakes"]},
            ],
            "expected_ownership_cost_annual": ownership_cost,
            "at": _now(),
        }
        return self.store.vi_recommendations.save(rid, result)

    def status(self) -> dict[str, Any]:
        return {"recommendations": self.store.vi_recommendations.count()}
