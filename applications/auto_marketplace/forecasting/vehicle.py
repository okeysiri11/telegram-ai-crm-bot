# Vehicle Forecasting Engine — future value, maintenance, demand (Sprint 10.3).

from __future__ import annotations

from applications.auto_marketplace.ai.models import VehicleForecast
from applications.auto_marketplace.pricing_ai.engine import PricingAIEngine, pricing_ai_engine
from applications.auto_marketplace.risk.engine import RiskEngine, risk_engine
from applications.auto_marketplace.shared.exceptions import ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class VehicleForecastEngine:
    def __init__(
        self,
        store: MarketplaceStore | None = None,
        pricing: PricingAIEngine | None = None,
        risk: RiskEngine | None = None,
    ) -> None:
        self._store = store or marketplace_store
        self._pricing = pricing or pricing_ai_engine
        self._risk = risk or risk_engine

    def forecast(
        self,
        *,
        vehicle_id: str = "",
        vin: str = "",
        year: int = 2020,
        mileage_km: int = 50000,
        base_price: float = 0.0,
        horizon_months: int = 12,
        currency: str = "USD",
    ) -> VehicleForecast:
        if not vehicle_id and not vin and base_price <= 0:
            raise ValidationError("vehicle_id, vin, or base_price is required")
        price = self._pricing.analyze(
            vehicle_id=vehicle_id, vin=vin, year=year, mileage_km=mileage_km, base_price=base_price, currency=currency
        )
        risk = self._risk.score_vehicle(vehicle_id=vehicle_id, year=year, mileage_km=mileage_km)
        months = max(1, horizon_months)
        future = round(price.market_value * (1 - price.depreciation_12m / max(price.market_value, 1) * (months / 12)), 2)
        maintenance = round(900 + mileage_km / 1000 * 8, 2)
        ownership = round(maintenance + price.market_value * 0.05 + 900, 2)
        demand = "high" if year >= 2022 and mileage_km < 40000 else "medium" if year >= 2018 else "low"
        result = VehicleForecast(
            vehicle_id=vehicle_id,
            vin=vin,
            future_value=future,
            maintenance_cost_12m=maintenance,
            repair_probability=round(min(0.85, 0.15 + risk["risk_score"]), 3),
            insurance_risk=risk["insurance_risk"],
            ownership_cost_12m=ownership,
            market_demand=demand,
            currency=currency,
            horizon_months=months,
            confidence=price.confidence,
        )
        return self._store.vehicle_forecasts.save(result.forecast_id, result)

    def metrics(self) -> dict:
        return {"vehicle_forecasts": self._store.vehicle_forecasts.count()}


vehicle_forecast_engine = VehicleForecastEngine()
