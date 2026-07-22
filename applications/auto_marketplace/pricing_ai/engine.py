# Pricing AI Engine — market/fair/dealer/wholesale/retail/trend/depreciation.

from __future__ import annotations

from applications.auto_marketplace.ai.models import AIPriceInsight
from applications.auto_marketplace.shared.exceptions import ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class PricingAIEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def analyze(
        self,
        *,
        vehicle_id: str = "",
        vin: str = "",
        year: int = 2020,
        mileage_km: int = 50000,
        base_price: float = 0.0,
        currency: str = "USD",
    ) -> AIPriceInsight:
        if not vehicle_id and not vin and base_price <= 0:
            raise ValidationError("vehicle_id, vin, or base_price is required")
        age = max(0, 2026 - year)
        mileage_factor = max(0.45, 1.0 - mileage_km / 350_000)
        age_factor = max(0.4, 1.0 - age * 0.045)
        market = round((base_price or 20000) * age_factor * mileage_factor, 2)
        fair = round(market * 1.0, 2)
        dealer = round(market * 1.06, 2)
        retail = round(market * 1.12, 2)
        wholesale = round(market * 0.88, 2)
        predicted = round(market * (0.98 if age > 3 else 1.01), 2)
        dep = round(market * 0.12, 2)
        residual = round(market * (0.55 if age < 5 else 0.4), 2)
        trend = "declining" if age > 4 or mileage_km > 100000 else "stable" if age > 1 else "rising"
        insight = AIPriceInsight(
            vehicle_id=vehicle_id,
            vin=vin,
            market_value=market,
            fair_price=fair,
            dealer_price=dealer,
            wholesale_price=wholesale,
            retail_price=retail,
            predicted_price=predicted,
            trend=trend,
            depreciation_12m=dep,
            residual_value_36m=residual,
            currency=currency,
            confidence=round(0.68 + min(0.2, mileage_factor * 0.2), 2),
        )
        return self._store.ai_price_insights.save(insight.insight_id, insight)

    def metrics(self) -> dict:
        return {"price_insights": self._store.ai_price_insights.count()}


pricing_ai_engine = PricingAIEngine()
