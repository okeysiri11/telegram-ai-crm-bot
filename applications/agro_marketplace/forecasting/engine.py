# Forecasting engine — price, demand, supply, harvest, season, risk.

from __future__ import annotations

import time
from typing import Any

from events.publisher import publish

from applications.agro_marketplace.ai.events import DemandPredictedEvent, ForecastCompletedEvent, PriceEstimatedEvent
from applications.agro_marketplace.ai.models import ForecastKind, ForecastResult
from applications.agro_marketplace.integrations.platform_bridge import PlatformBridge, platform_bridge
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class ForecastingEngine:
    def __init__(
        self,
        store: AgroStore | None = None,
        platform: PlatformBridge | None = None,
    ) -> None:
        self._store = store or agro_store
        self._platform = platform or platform_bridge

    async def _complete(self, result: ForecastResult) -> ForecastResult:
        saved = self._store.forecasts.save(result.forecast_id, result)
        await publish(
            ForecastCompletedEvent(
                forecast_id=saved.forecast_id,
                kind=saved.kind.value,
                subject=saved.subject,
                confidence=saved.confidence,
            )
        )
        await self._platform.remember_context(
            f"forecast:{saved.kind.value}:{saved.subject}",
            saved.to_dict(),
        )
        return saved

    def _series(self, base: float, horizon_days: int, drift: float) -> list[dict[str, Any]]:
        points = []
        value = base
        now = time.time()
        step = max(1, horizon_days // 5)
        for i in range(0, horizon_days + 1, step):
            points.append({"day_offset": i, "value": round(value, 2), "at": now + i * 86400})
            value *= 1.0 + drift
        return points

    async def forecast_price(
        self,
        subject: str,
        *,
        region: str = "",
        horizon_days: int = 30,
        base_price: float | None = None,
    ) -> ForecastResult:
        prices = [
            o.price
            for o in self._store.sales_offers.list_all()
            if (o.crop_id == subject or o.product_id == subject) and o.price > 0
        ]
        if not prices:
            prices = [
                p.price
                for p in self._store.agro_products.list_all()
                if (p.crop_id == subject or p.name.lower() == subject.lower()) and p.price > 0
            ]
        base = base_price if base_price is not None else (sum(prices) / len(prices) if prices else 100.0)
        result = ForecastResult(
            kind=ForecastKind.PRICE,
            subject=subject,
            region=region,
            horizon_days=horizon_days,
            values=self._series(base, horizon_days, drift=0.01),
            confidence=0.7 if prices else 0.45,
            metadata={"sample_size": len(prices), "base": base},
        )
        saved = await self._complete(result)
        await publish(
            PriceEstimatedEvent(product_id=subject, estimated_price=base, currency="USD")
        )
        return saved

    async def forecast_demand(
        self,
        subject: str,
        *,
        region: str = "",
        horizon_days: int = 30,
    ) -> ForecastResult:
        requests = [
            r
            for r in self._store.purchase_requests.list_all()
            if r.crop_id == subject or r.product_id == subject
        ]
        base = sum(r.quantity for r in requests) or 10.0
        if region:
            region_reqs = [r for r in requests if r.region.lower() == region.lower()]
            if region_reqs:
                base = sum(r.quantity for r in region_reqs)
        result = ForecastResult(
            kind=ForecastKind.DEMAND,
            subject=subject,
            region=region,
            horizon_days=horizon_days,
            values=self._series(base, horizon_days, drift=0.02),
            confidence=0.65 if requests else 0.4,
            metadata={"open_requests": len(requests)},
        )
        saved = await self._complete(result)
        await publish(
            DemandPredictedEvent(subject=subject, region=region, predicted_demand=base)
        )
        return saved

    async def forecast_supply(
        self,
        subject: str,
        *,
        region: str = "",
        horizon_days: int = 30,
    ) -> ForecastResult:
        offers = [
            o
            for o in self._store.sales_offers.list_all()
            if o.crop_id == subject or o.product_id == subject
        ]
        inventory = [
            i
            for i in self._store.inventory_items.list_all()
            if i.product_id == subject
        ]
        base = sum(o.quantity for o in offers) + sum(i.available_quantity for i in inventory)
        if base <= 0:
            base = 8.0
        result = ForecastResult(
            kind=ForecastKind.SUPPLY,
            subject=subject,
            region=region,
            horizon_days=horizon_days,
            values=self._series(base, horizon_days, drift=-0.005),
            confidence=0.6 if offers or inventory else 0.4,
            metadata={"offers": len(offers), "inventory_items": len(inventory)},
        )
        return await self._complete(result)

    async def forecast_harvest(
        self,
        subject: str,
        *,
        region: str = "",
        horizon_days: int = 90,
    ) -> ForecastResult:
        """Harvest forecasting interface — uses harvest records when available."""
        harvests = [
            h
            for h in self._store.harvest_records.list_all()
            if h.crop_id == subject and (not region or h.region.lower() == region.lower())
        ]
        base = sum(h.quantity for h in harvests) or 12.0
        avg_yield = (
            sum(h.yield_per_hectare for h in harvests) / len(harvests) if harvests else 0.0
        )
        result = ForecastResult(
            kind=ForecastKind.HARVEST,
            subject=subject,
            region=region,
            horizon_days=horizon_days,
            values=self._series(base, horizon_days, drift=0.015),
            confidence=0.55 if harvests else 0.35,
            metadata={"harvest_samples": len(harvests), "avg_yield_per_hectare": avg_yield},
        )
        return await self._complete(result)

    async def season_plan(self, crop: str, *, region: str = "") -> ForecastResult:
        result = ForecastResult(
            kind=ForecastKind.SEASON,
            subject=crop,
            region=region,
            horizon_days=180,
            values=[
                {"phase": "prepare", "month_offset": 0},
                {"phase": "plant", "month_offset": 1},
                {"phase": "grow", "month_offset": 3},
                {"phase": "harvest", "month_offset": 5},
                {"phase": "market", "month_offset": 6},
            ],
            confidence=0.5,
            metadata={"crop": crop, "region": region},
        )
        return await self._complete(result)

    async def estimate_risk(self, subject: str, *, region: str = "") -> ForecastResult:
        moisture_risk = 0.0
        harvests = [h for h in self._store.harvest_records.list_all() if h.crop_id == subject]
        if harvests:
            moisture_risk = sum(1 for h in harvests if h.moisture_pct > 14) / len(harvests)
        util_risk = 0.0
        warehouses = self._store.agro_warehouses.list_all()
        if warehouses:
            utils = [
                (w.used_tons / w.capacity_tons) if w.capacity_tons else 0.0 for w in warehouses
            ]
            util_risk = sum(1 for u in utils if u > 0.9) / len(utils)
        score = round(min(1.0, 0.4 * moisture_risk + 0.4 * util_risk + 0.2), 2)
        result = ForecastResult(
            kind=ForecastKind.RISK,
            subject=subject,
            region=region,
            horizon_days=30,
            values=[{"risk_score": score, "moisture_risk": moisture_risk, "capacity_risk": util_risk}],
            confidence=0.6,
            metadata={"interpretation": "higher is riskier"},
        )
        return await self._complete(result)

    def list_forecasts(self, *, kind: ForecastKind | None = None) -> list[ForecastResult]:
        items = self._store.forecasts.list_all()
        if kind:
            items = [f for f in items if f.kind == kind]
        return items


forecasting_engine = ForecastingEngine()
