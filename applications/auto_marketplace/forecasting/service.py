# Forecasting service — sales, revenue, inventory, demand, cash flow, growth.

from __future__ import annotations

from events.publisher import publish

from applications.auto_marketplace.business_intelligence.events import ForecastCompletedEvent
from applications.auto_marketplace.business_intelligence.models import ForecastResult
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class ForecastingService:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    async def _base_forecast(self, forecast_type: str, base_value: float, *, period_days: int = 30) -> ForecastResult:
        growth = 1.05 if forecast_type in {"sales", "revenue", "growth"} else 1.02
        predictions = []
        value = base_value
        for week in range(1, 5):
            value *= growth ** 0.25
            predictions.append({"period": f"week_{week}", "value": round(value, 2)})
        result = ForecastResult(
            forecast_type=forecast_type,
            period_days=period_days,
            predictions=predictions,
            confidence=0.75,
        )
        self._store.bi_forecasts.save(result.forecast_id, result)
        await publish(
            ForecastCompletedEvent(
                forecast_id=result.forecast_id,
                forecast_type=forecast_type,
                confidence=result.confidence,
            )
        )
        return result

    async def sales_forecast(self, *, period_days: int = 30) -> ForecastResult:
        won = len([d for d in self._store.crm_deals.list_all() if d.stage.value == "closed_won"])
        return await self._base_forecast("sales", float(max(won, 1)), period_days=period_days)

    async def revenue_forecast(self, *, period_days: int = 30) -> ForecastResult:
        revenue = sum(p.amount for p in self._store.finance_payments.list_all() if p.status == "completed")
        return await self._base_forecast("revenue", revenue or 10000, period_days=period_days)

    async def inventory_forecast(self, *, period_days: int = 30) -> ForecastResult:
        count = self._store.catalog_vehicles.count() or self._store.vehicles.count()
        return await self._base_forecast("inventory", float(max(count, 1)), period_days=period_days)

    async def demand_forecast(self, *, period_days: int = 30) -> ForecastResult:
        leads = self._store.crm_leads.count()
        return await self._base_forecast("demand", float(max(leads, 1)), period_days=period_days)

    async def cashflow_forecast(self, *, period_days: int = 30) -> ForecastResult:
        inflow = sum(p.amount for p in self._store.finance_payments.list_all() if p.status == "completed")
        outflow = sum(r.amount for r in self._store.refunds.list_all())
        return await self._base_forecast("cashflow", inflow - outflow, period_days=period_days)

    async def growth_forecast(self, *, period_days: int = 30) -> ForecastResult:
        customers = self._store.customer_profiles.count()
        return await self._base_forecast("growth", float(max(customers, 1)), period_days=period_days)

    async def all_forecasts(self, *, period_days: int = 30) -> dict[str, ForecastResult]:
        return {
            "sales": await self.sales_forecast(period_days=period_days),
            "revenue": await self.revenue_forecast(period_days=period_days),
            "inventory": await self.inventory_forecast(period_days=period_days),
            "demand": await self.demand_forecast(period_days=period_days),
            "cashflow": await self.cashflow_forecast(period_days=period_days),
            "growth": await self.growth_forecast(period_days=period_days),
        }


forecasting_service = ForecastingService()
