# Smart Recommendation Engine — Sprint 10.3 personal/fleet/family recommendations.

from __future__ import annotations

from applications.auto_marketplace.ai.models import RecommendationKind, SmartRecommendation
from applications.auto_marketplace.matching.engine import MatchingEngine, matching_engine
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class SmartRecommendationEngine:
    def __init__(
        self,
        store: MarketplaceStore | None = None,
        matching: MatchingEngine | None = None,
    ) -> None:
        self._store = store or marketplace_store
        self._matching = matching or matching_engine

    def _persist(self, items: list[SmartRecommendation]) -> list[SmartRecommendation]:
        for item in items:
            self._store.smart_recommendations.save(item.recommendation_id, item)
        return items

    def personal(self, buyer_id: str, preferences: dict | None = None, *, limit: int = 5) -> list[SmartRecommendation]:
        prefs = preferences or {}
        matches = self._matching.match_preferences(prefs, limit=limit)
        items = [
            SmartRecommendation(
                kind=RecommendationKind.PERSONAL,
                buyer_id=buyer_id,
                vehicle_id=m["vehicle_id"],
                score=m["score"],
                reason="Personalized match to preferences and budget",
                payload=m.get("vehicle") or {},
            )
            for m in matches
        ]
        return self._persist(items)

    def similar(self, vehicle_id: str, *, limit: int = 5) -> list[SmartRecommendation]:
        items = [
            SmartRecommendation(
                kind=RecommendationKind.SIMILAR,
                vehicle_id=m["vehicle_id"],
                score=m["score"],
                reason="Similar make/price profile",
                payload=m.get("vehicle") or {},
            )
            for m in self._matching.similar(vehicle_id, limit=limit)
        ]
        return self._persist(items)

    def alternatives(self, vehicle_id: str, *, limit: int = 5) -> list[SmartRecommendation]:
        similar = self.similar(vehicle_id, limit=limit)
        for item in similar:
            item.kind = RecommendationKind.ALTERNATIVE
            item.reason = "Alternative vehicle in similar segment"
            self._store.smart_recommendations.save(item.recommendation_id, item)
        return similar

    def budget_optimize(self, buyer_id: str, budget: float, *, limit: int = 5) -> list[SmartRecommendation]:
        return self.personal(buyer_id, {"budget_max": budget}, limit=limit)

    def ownership_cost(self, vehicle_id: str) -> SmartRecommendation:
        vehicle = self._store.vehicles.get(vehicle_id) or self._store.catalog_vehicles.get(vehicle_id)
        price = getattr(vehicle, "price", 15000) if vehicle else 15000
        annual = round(price * 0.08 + 1800, 2)
        item = SmartRecommendation(
            kind=RecommendationKind.OWNERSHIP_COST,
            vehicle_id=vehicle_id,
            score=70.0,
            reason="Predicted 12-month ownership cost",
            payload={"annual_cost": annual, "fuel": round(price * 0.03, 2), "insurance": 900, "maintenance": 900},
        )
        return self._persist([item])[0]

    def family(self, buyer_id: str, *, seats: int = 5, limit: int = 5) -> list[SmartRecommendation]:
        return self.personal(buyer_id, {"budget_max": 80000, "body": "suv" if seats >= 5 else "sedan"}, limit=limit)

    def commercial(self, buyer_id: str, *, limit: int = 5) -> list[SmartRecommendation]:
        items = self.personal(buyer_id, {"budget_max": 120000, "body": "van"}, limit=limit)
        for item in items:
            item.kind = RecommendationKind.COMMERCIAL
            item.reason = "Commercial duty recommendation"
            self._store.smart_recommendations.save(item.recommendation_id, item)
        return items

    def fleet(self, buyer_id: str, *, fleet_size: int = 5, limit: int = 5) -> list[SmartRecommendation]:
        items = self.personal(buyer_id, {"budget_max": 40000 * fleet_size, "body": "sedan"}, limit=limit)
        for item in items:
            item.kind = RecommendationKind.FLEET
            item.reason = f"Fleet recommendation for {fleet_size} units"
            item.payload["fleet_size"] = fleet_size
            self._store.smart_recommendations.save(item.recommendation_id, item)
        return items

    def metrics(self) -> dict:
        return {"smart_recommendations": self._store.smart_recommendations.count()}


smart_recommendation_engine = SmartRecommendationEngine()
