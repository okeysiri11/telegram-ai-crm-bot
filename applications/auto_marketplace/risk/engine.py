# Risk Engine — insurance/ownership/fraud-oriented vehicle risk scoring.

from __future__ import annotations

from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class RiskEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def score_vehicle(self, *, vehicle_id: str = "", year: int = 2020, mileage_km: int = 50000, accidents: int = 0) -> dict:
        age = max(0, 2026 - year)
        score = 0.2 + age * 0.03 + mileage_km / 500_000 + accidents * 0.15
        score = round(min(score, 0.95), 3)
        level = "high" if score >= 0.65 else "medium" if score >= 0.35 else "low"
        result = {
            "vehicle_id": vehicle_id,
            "risk_score": score,
            "level": level,
            "insurance_risk": round(score * 0.9, 3),
            "drivers": {"age": age, "mileage_km": mileage_km, "accidents": accidents},
        }
        key = vehicle_id or f"risk-{year}-{mileage_km}"
        self._store.ai_risk_scores.save(key, result)
        return result

    def metrics(self) -> dict:
        return {"risk_scores": self._store.ai_risk_scores.count()}


risk_engine = RiskEngine()
