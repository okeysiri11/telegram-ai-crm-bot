# PricingService and RecommendationService.

from __future__ import annotations

from typing import Any

from applications.auto_marketplace.shared.models import TradeIn, Vehicle
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class PricingService:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def estimate_vehicle_price(self, vehicle: Vehicle) -> float:
        spec = vehicle.specification
        base = max(spec.year - 2000, 1) * 1000.0
        mileage_factor = max(0.5, 1.0 - spec.mileage_km / 300_000)
        return round(vehicle.price or base * mileage_factor, 2)

    def estimate_trade_in(self, trade_in: TradeIn) -> float:
        spec = trade_in.specification
        base = max(spec.year - 2000, 1) * 800.0
        mileage_factor = max(0.4, 1.0 - spec.mileage_km / 350_000)
        value = round(base * mileage_factor, 2)
        trade_in.estimated_value = value
        self._store.trade_ins.save(trade_in.trade_in_id, trade_in)
        return value

    def market_adjusted_price(self, vehicle_id: str, *, demand_factor: float = 1.0) -> float:
        vehicle = self._store.vehicles.get(vehicle_id)
        if vehicle is None:
            return 0.0
        base = self.estimate_vehicle_price(vehicle)
        return round(base * demand_factor, 2)

    def record_price(self, vehicle_id: str, price: float, *, currency: str = "USD", reason: str = "") -> dict:
        from applications.auto_marketplace.foundation.models import PriceHistory

        entry = PriceHistory(vehicle_id=vehicle_id, price=price, currency=currency, reason=reason)
        self._store.price_history.save(entry.entry_id, entry)
        vehicle = self._store.vehicles.get(vehicle_id)
        if vehicle is not None:
            vehicle.price = price
            vehicle.currency = currency
            self._store.vehicles.save(vehicle_id, vehicle)
        return entry.to_dict()

    def price_history(self, vehicle_id: str) -> list[dict]:
        return [
            e.to_dict()
            for e in self._store.price_history.list_all()
            if e.vehicle_id == vehicle_id
        ]


class RecommendationService:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store
        self._pricing = PricingService(store)

    def recommend_for_customer(self, customer_id: str, *, limit: int = 5) -> list[dict[str, Any]]:
        customer = self._store.customers.get(customer_id)
        prefs = customer.preferences if customer else {}
        budget = float(prefs.get("budget_max", 1_000_000))
        make = str(prefs.get("make", "")).lower()

        scored: list[tuple[float, Vehicle]] = []
        for vehicle in self._store.vehicles.list_all():
            if vehicle.price > budget:
                continue
            if make and vehicle.specification.make.lower() != make:
                continue
            score = budget - vehicle.price
            scored.append((score, vehicle))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {"vehicle": v.to_dict(), "score": s, "estimated_price": self._pricing.estimate_vehicle_price(v)}
            for s, v in scored[:limit]
        ]


pricing_service = PricingService()
recommendation_service = RecommendationService()
