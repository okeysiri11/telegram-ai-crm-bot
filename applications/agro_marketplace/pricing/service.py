# PricingService — quotes, catalog pricing, AI price estimation hooks.

from __future__ import annotations

from typing import Any

from applications.agro_marketplace.product_catalog.ai_integration import CatalogAIIntegration, catalog_ai
from applications.agro_marketplace.product_catalog.models import AvailabilityStatus
from applications.agro_marketplace.shared.models import ProductStatus
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class PricingService:
    def __init__(
        self,
        store: AgroStore | None = None,
        ai: CatalogAIIntegration | None = None,
    ) -> None:
        self._store = store or agro_store
        self._ai = ai or catalog_ai

    def quote(self, product_id: str, quantity: float) -> dict[str, Any]:
        product = self._store.agro_products.get(product_id) or self._store.products.get(product_id)
        if product is None:
            return {"error": "product_not_found"}
        unit = product.price
        discount = 0.05 if quantity >= 10 else 0.0
        effective = unit * (1 - discount)
        currency = getattr(product, "currency", "USD")
        return {
            "product_id": product_id,
            "quantity": quantity,
            "unit_price": unit,
            "discount": discount,
            "effective_unit_price": effective,
            "total": effective * quantity,
            "currency": currency,
        }

    def market_average(self, *, category_id: str = "") -> float:
        agro = [
            p
            for p in self._store.agro_products.list_all()
            if p.status != AvailabilityStatus.ARCHIVED and (not category_id or p.category_id == category_id)
        ]
        if agro:
            return sum(p.price for p in agro) / len(agro)
        products = [
            p
            for p in self._store.products.list_all()
            if p.status == ProductStatus.LISTED and (not category_id or p.category_id == category_id)
        ]
        if not products:
            return 0.0
        return sum(p.price for p in products) / len(products)

    def recommend_for_buyer(self, buyer_id: str, *, budget: float | None = None) -> list[dict[str, Any]]:
        products = [
            p for p in self._store.agro_products.list_all() if p.status == AvailabilityStatus.AVAILABLE
        ]
        if not products:
            products = [p for p in self._store.products.list_all() if p.status == ProductStatus.LISTED]  # type: ignore[assignment]
        if budget is not None:
            products = [p for p in products if p.price <= budget]
        products = sorted(products, key=lambda p: p.price)
        return [p.to_dict() for p in products[:10]]

    async def estimate_price(self, product_id: str) -> dict[str, Any]:
        product = self._store.agro_products.get(product_id)
        if product is None:
            return {"error": "product_not_found"}
        estimated = await self._ai.estimate_price(product)
        demand = await self._ai.estimate_demand(product)
        return {
            "product_id": product_id,
            "estimated_price": estimated,
            "current_price": product.price,
            "demand": demand,
        }


pricing_service = PricingService()
