# Valuation Engine — market / dealer / wholesale / retail / AI pricing.

from __future__ import annotations

import time

from applications.auto_marketplace.marketplace.models import MarketValuation
from applications.auto_marketplace.shared.exceptions import ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class ValuationEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def value_vehicle(
        self,
        *,
        vehicle_id: str = "",
        vin: str = "",
        year: int = 2020,
        mileage_km: int = 50000,
        base_price: float = 0.0,
        currency: str = "USD",
    ) -> MarketValuation:
        if not vehicle_id and not vin:
            raise ValidationError("vehicle_id or vin is required")
        age = max(0, 2026 - year)
        mileage_factor = max(0.45, 1.0 - mileage_km / 350_000)
        age_factor = max(0.4, 1.0 - age * 0.04)
        anchor = base_price or (18000 * age_factor * mileage_factor)
        average = round(anchor, 2)
        dealer = round(average * 1.05, 2)
        retail = round(average * 1.12, 2)
        wholesale = round(average * 0.88, 2)
        ai_val = round((average + dealer + wholesale) / 3 * 1.01, 2)
        valuation = MarketValuation(
            vehicle_id=vehicle_id,
            vin=vin,
            average_price=average,
            dealer_price=dealer,
            wholesale_price=wholesale,
            retail_price=retail,
            ai_valuation=ai_val,
            currency=currency,
            confidence=round(0.65 + min(0.25, mileage_factor * 0.2), 2),
            history=[{"price": average, "kind": "market", "at": time.time()}],
        )
        # Persist price history entry for vehicle when known
        if vehicle_id:
            from applications.auto_marketplace.foundation.models import PriceHistory

            entry = PriceHistory(vehicle_id=vehicle_id, price=ai_val, currency=currency, reason="ai_valuation")
            self._store.price_history.save(entry.entry_id, entry)
        return self._store.market_valuations.save(valuation.valuation_id, valuation)

    def list_valuations(self, *, vehicle_id: str = "") -> list[MarketValuation]:
        items = self._store.market_valuations.list_all()
        if vehicle_id:
            items = [v for v in items if v.vehicle_id == vehicle_id]
        return items

    def metrics(self) -> dict:
        return {"valuations": self._store.market_valuations.count()}


valuation_engine = ValuationEngine()
