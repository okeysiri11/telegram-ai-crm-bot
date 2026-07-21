# AnalyticsService — marketplace metrics and dashboard data.

from __future__ import annotations

from typing import Any

from applications.agro_marketplace.shared.models import OrderStatus, ProductStatus
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class AnalyticsService:
    def __init__(self, store: AgroStore | None = None) -> None:
        self._store = store or agro_store

    def dashboard_metrics(self) -> dict[str, Any]:
        orders = self._store.orders.list_all()
        products = self._store.products.list_all()
        gmv = sum(o.total for o in orders if o.status != OrderStatus.CANCELLED)
        return {
            "farmers": self._store.farmers.count(),
            "buyers": self._store.buyers.count(),
            "suppliers": self._store.suppliers.count(),
            "products": len(products),
            "listed_products": sum(1 for p in products if p.status == ProductStatus.LISTED),
            "orders": len(orders),
            "gmv": gmv,
            "warehouses": self._store.warehouses.count(),
            "export_shipments": self._store.export_shipments.count(),
            "deliveries": self._store.deliveries.count(),
            "harvests": self._store.harvests.count(),
        }

    def orders_by_status(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for order in self._store.orders.list_all():
            key = order.status.value
            counts[key] = counts.get(key, 0) + 1
        return counts


analytics_service = AnalyticsService()
