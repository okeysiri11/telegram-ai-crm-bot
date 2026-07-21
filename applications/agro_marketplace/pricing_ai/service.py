# Pricing AI — price estimation and advisory.

from __future__ import annotations

from typing import Any

from events.publisher import publish

from applications.agro_marketplace.ai.events import PriceEstimatedEvent
from applications.agro_marketplace.forecasting.engine import ForecastingEngine, forecasting_engine
from applications.agro_marketplace.marketplace.ai_integration import TradingAIIntegration, trading_ai
from applications.agro_marketplace.shared.exceptions import NotFoundError
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class PricingAIService:
    def __init__(
        self,
        store: AgroStore | None = None,
        forecasting: ForecastingEngine | None = None,
        trading_ai_svc: TradingAIIntegration | None = None,
    ) -> None:
        self._store = store or agro_store
        self._forecasting = forecasting or forecasting_engine
        self._trading_ai = trading_ai_svc or trading_ai

    async def estimate_price(self, product_id: str) -> dict[str, Any]:
        product = self._store.agro_products.get(product_id)
        if product is None:
            raise NotFoundError("AgriculturalProduct", product_id)
        forecast = await self._forecasting.forecast_price(
            product.crop_id or product.name,
            region=product.region,
            base_price=product.price or None,
        )
        estimated = float(forecast.values[0]["value"]) if forecast.values else product.price
        if product.attributes.get("organic"):
            estimated *= 1.15
        await publish(
            PriceEstimatedEvent(
                product_id=product_id,
                estimated_price=round(estimated, 2),
                currency=product.currency,
            )
        )
        return {
            "product_id": product_id,
            "estimated_price": round(estimated, 2),
            "current_price": product.price,
            "forecast_id": forecast.forecast_id,
            "confidence": forecast.confidence,
        }

    async def advise_offer_price(self, offer_id: str) -> dict[str, Any]:
        offer = self._store.sales_offers.get(offer_id)
        if offer is None:
            raise NotFoundError("SalesOffer", offer_id)
        prices = [
            o.price for o in self._store.sales_offers.list_all() if o.crop_id == offer.crop_id and o.price > 0
        ]
        avg = sum(prices) / len(prices) if prices else offer.price
        return await self._trading_ai.recommend_price(offer, market_avg=avg)


pricing_ai_service = PricingAIService()
