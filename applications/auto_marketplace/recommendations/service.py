# AI Recommendation Engine — personalized vehicle suggestions.

from __future__ import annotations

from typing import Any

from events.publisher import publish

from applications.auto_marketplace.ai_sales.events import RecommendationGeneratedEvent
from applications.auto_marketplace.ai_sales.models import VehicleRecommendation
from applications.auto_marketplace.customer_intelligence.service import CustomerIntelligenceService, customer_intelligence_service
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class AIRecommendationEngine:
    def __init__(
        self,
        store: MarketplaceStore | None = None,
        intelligence: CustomerIntelligenceService | None = None,
    ) -> None:
        self._store = store or marketplace_store
        self._intelligence = intelligence or customer_intelligence_service

    async def _score_vehicle(self, vehicle: Any, profile_budget: float, preferred_makes: list[str]) -> float:
        score = 50.0
        price = getattr(vehicle, "price", 0) or 0
        if price <= profile_budget:
            score += 20
        brand = getattr(vehicle, "brand", "") or getattr(getattr(vehicle, "specification", None), "make", "")
        if preferred_makes and brand.lower() in [m.lower() for m in preferred_makes]:
            score += 25
        mileage = getattr(vehicle, "mileage_km", 0) or 0
        if mileage < 50000:
            score += 10
        return min(score, 100.0)

    def _catalog_vehicles(self) -> list[Any]:
        catalog = self._store.catalog_vehicles.list_all()
        if catalog:
            return catalog
        return self._store.vehicles.list_all()

    async def personalized(self, customer_id: str, *, limit: int = 5) -> list[VehicleRecommendation]:
        profile = await self._intelligence.analyze_profile(customer_id)
        results: list[VehicleRecommendation] = []
        for vehicle in self._catalog_vehicles():
            price = getattr(vehicle, "price", 0) or 0
            if price > profile.budget_max:
                continue
            vid = getattr(vehicle, "vehicle_id", "") or getattr(vehicle, "catalog_vehicle_id", "")
            score = await self._score_vehicle(vehicle, profile.budget_max, profile.preferred_makes)
            vdict = vehicle.to_dict() if hasattr(vehicle, "to_dict") else {"vehicle_id": vid}
            results.append(
                VehicleRecommendation(
                    vehicle_id=vid,
                    recommendation_type="personalized",
                    score=score,
                    reason="Matches budget and preferences",
                    vehicle=vdict,
                )
            )
        results.sort(key=lambda r: r.score, reverse=True)
        top = results[:limit]
        await publish(
            RecommendationGeneratedEvent(
                customer_id=customer_id,
                recommendation_type="personalized",
                vehicle_ids=[r.vehicle_id for r in top],
            )
        )
        return top

    async def alternatives(self, vehicle_id: str, *, limit: int = 5) -> list[VehicleRecommendation]:
        source = self._store.catalog_vehicles.get(vehicle_id) or self._store.vehicles.get(vehicle_id)
        if source is None:
            return []
        brand = getattr(source, "brand", "") or ""
        model = getattr(source, "model", "") or ""
        price = getattr(source, "price", 0) or 0
        results: list[VehicleRecommendation] = []
        for vehicle in self._catalog_vehicles():
            vid = getattr(vehicle, "vehicle_id", "") or getattr(vehicle, "catalog_vehicle_id", "")
            if vid == vehicle_id:
                continue
            vprice = getattr(vehicle, "price", 0) or 0
            if abs(vprice - price) / max(price, 1) > 0.3:
                continue
            vbrand = getattr(vehicle, "brand", "")
            score = 60.0 + (15 if vbrand == brand else 0)
            results.append(
                VehicleRecommendation(
                    vehicle_id=vid,
                    recommendation_type="alternative",
                    score=score,
                    reason=f"Similar to {brand} {model}",
                    vehicle=vehicle.to_dict() if hasattr(vehicle, "to_dict") else {},
                )
            )
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]

    async def upsell(self, customer_id: str, vehicle_id: str) -> list[VehicleRecommendation]:
        source = self._store.catalog_vehicles.get(vehicle_id) or self._store.vehicles.get(vehicle_id)
        base_price = getattr(source, "price", 0) if source else 0
        results: list[VehicleRecommendation] = []
        for vehicle in self._catalog_vehicles():
            vid = getattr(vehicle, "vehicle_id", "") or getattr(vehicle, "catalog_vehicle_id", "")
            price = getattr(vehicle, "price", 0) or 0
            if price <= base_price or price > base_price * 1.4:
                continue
            results.append(
                VehicleRecommendation(
                    vehicle_id=vid,
                    recommendation_type="upsell",
                    score=70.0,
                    reason="Premium upgrade with enhanced features",
                    vehicle=vehicle.to_dict() if hasattr(vehicle, "to_dict") else {},
                )
            )
        return results[:3]

    async def cross_sell(self, customer_id: str) -> list[VehicleRecommendation]:
        profile = await self._intelligence.analyze_profile(customer_id)
        body_types = profile.preferred_body_types or ["suv"]
        target = body_types[0] if body_types else "suv"
        results: list[VehicleRecommendation] = []
        for vehicle in self._catalog_vehicles():
            category = getattr(vehicle, "category", "") or getattr(vehicle, "body_type", "")
            if target.lower() not in str(category).lower():
                continue
            vid = getattr(vehicle, "vehicle_id", "") or getattr(vehicle, "catalog_vehicle_id", "")
            results.append(
                VehicleRecommendation(
                    vehicle_id=vid,
                    recommendation_type="cross_sell",
                    score=55.0,
                    reason=f"Complementary {target} option",
                    vehicle=vehicle.to_dict() if hasattr(vehicle, "to_dict") else {},
                )
            )
        return results[:3]

    async def trade_in_suggestions(self, customer_id: str) -> dict[str, Any]:
        profile = await self._intelligence.analyze_profile(customer_id)
        trade_ins = [t for t in self._store.trade_ins.list_all() if getattr(t, "customer_id", "") == customer_id]
        estimated = sum(getattr(t, "estimated_value", 0) or 0 for t in trade_ins)
        if not estimated:
            estimated = profile.budget_max * 0.2
        return {
            "customer_id": customer_id,
            "estimated_trade_in_value": round(estimated, 2),
            "recommendation": "Apply trade-in credit toward next purchase",
        }

    async def accessory_recommendations(self, vehicle_id: str) -> list[dict[str, str]]:
        return [
            {"name": "All-weather floor mats", "category": "interior"},
            {"name": "Extended warranty", "category": "protection"},
            {"name": "Roof rack", "category": "exterior"},
        ]


ai_recommendation_engine = AIRecommendationEngine()
