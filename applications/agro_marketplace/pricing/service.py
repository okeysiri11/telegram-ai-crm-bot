# PricingService — price quotes and recommendations.

from __future__ import annotations

from typing import Any

from applications.agro_marketplace.shared.models import ProductStatus
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class PricingService:
    def __init__(self, store: AgroStore | None = None) -> None:
        self._store = store or agro_store

    def quote(self, product_id: str, quantity: float) -> dict[str, Any]:
        product = self._store.products.get(product_id)
        if product is None:
            return {"error": "product_not_found"}
        unit = product.price
        discount = 0.05 if quantity >= 10 else 0.0
        effective = unit * (1 - discount)
        return {
            "product_id": product_id,
            "quantity": quantity,
            "unit_price": unit,
            "discount": discount,
            "effective_unit_price": effective,
            "total": effective * quantity,
            "currency": product.currency,
        }

    def market_average(self, *, category_id: str = "") -> float:
        products = [
            p
            for p in self._store.products.list_all()
            if p.status == ProductStatus.LISTED and (not category_id or p.category_id == category_id)
        ]
        if not products:
            return 0.0
        return sum(p.price for p in products) / len(products)

    def recommend_for_buyer(self, buyer_id: str, *, budget: float | None = None) -> list[dict[str, Any]]:
        products = [p for p in self._store.products.list_all() if p.status == ProductStatus.LISTED]
        if budget is not None:
            products = [p for p in products if p.price <= budget]
        products = sorted(products, key=lambda p: p.price)
        return [p.to_dict() for p in products[:10]]


pricing_service = PricingService()
