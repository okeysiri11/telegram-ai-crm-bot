# Domain analytics — sales, inventory, harvest, crop, demand, supply, pricing, export, customer, regional.

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
            "intl_shipments": self._store.intl_shipments.count(),
            "deliveries": self._store.deliveries.count(),
            "harvests": self._store.harvests.count(),
            "harvest_records": self._store.harvest_records.count(),
        }

    def orders_by_status(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for order in self._store.orders.list_all():
            key = order.status.value
            counts[key] = counts.get(key, 0) + 1
        return counts

    def ai_insights(self) -> dict[str, Any]:
        return {
            "recommendations": self._store.recommendations.count(),
            "forecasts": self._store.forecasts.count(),
            "agent_invocations": self._store.agent_invocations.count(),
            "knowledge_articles": self._store.knowledge_articles.count(),
            "executive_reports": self._store.executive_reports.count(),
            "ai_workflow_tasks": self._store.ai_workflow_tasks.count(),
            "marketplace_orders": self._store.marketplace_orders.count(),
            "sales_offers": self._store.sales_offers.count(),
            "purchase_requests": self._store.purchase_requests.count(),
            "insights": self._store.insights.count(),
            "anomalies": self._store.anomalies.count(),
            "kpi_snapshots": self._store.kpi_snapshots.count(),
        }

    def sales_analytics(self) -> dict[str, Any]:
        orders = [o for o in self._store.orders.list_all() if o.status != OrderStatus.CANCELLED]
        mp = self._store.marketplace_orders.list_all()
        gmv = sum(o.total for o in orders)
        return {
            "order_count": len(orders) + len(mp),
            "gmv": gmv,
            "avg_order_value": (gmv / len(orders)) if orders else 0.0,
            "offers": self._store.sales_offers.count(),
            "deals": self._store.marketplace_deals.count(),
        }

    def inventory_analytics(self) -> dict[str, Any]:
        items = self._store.inventory_items.list_all()
        qty = sum(getattr(i, "available_quantity", 0) or getattr(i, "quantity", 0) or 0 for i in items)
        return {
            "items": len(items),
            "available_quantity": qty,
            "warehouses": self._store.agro_warehouses.count() or self._store.warehouses.count(),
            "lots": self._store.storage_lots.count() if hasattr(self._store, "storage_lots") else 0,
        }

    def harvest_analytics(self) -> dict[str, Any]:
        records = self._store.harvest_records.list_all()
        legacy = self._store.harvests.list_all()
        qty = sum(getattr(h, "quantity", 0) or 0 for h in records)
        return {
            "records": len(records),
            "legacy_harvests": len(legacy),
            "total_quantity": qty,
            "avg_moisture": (
                sum(getattr(h, "moisture_pct", 0) or 0 for h in records) / len(records) if records else 0.0
            ),
        }

    def crop_analytics(self) -> dict[str, Any]:
        crops: dict[str, int] = {}
        for product in self._store.agro_products.list_all():
            crop = getattr(product, "crop_id", "") or "unknown"
            crops[crop] = crops.get(crop, 0) + 1
        for offer in self._store.sales_offers.list_all():
            crop = getattr(offer, "crop_id", "") or "unknown"
            crops[crop] = crops.get(crop, 0) + 1
        return {"by_crop": crops, "unique_crops": len(crops)}

    def demand_analytics(self) -> dict[str, Any]:
        requests = self._store.purchase_requests.list_all()
        qty = sum(getattr(r, "quantity", 0) or 0 for r in requests)
        return {
            "purchase_requests": len(requests),
            "requested_quantity": qty,
            "buyers": self._store.buyers.count(),
        }

    def supply_analytics(self) -> dict[str, Any]:
        offers = self._store.sales_offers.list_all()
        qty = sum(getattr(o, "quantity", 0) or 0 for o in offers)
        return {
            "sales_offers": len(offers),
            "offered_quantity": qty,
            "suppliers": self._store.suppliers.count(),
            "farmers": self._store.farmers.count(),
        }

    def pricing_analytics(self) -> dict[str, Any]:
        prices = [o.price for o in self._store.sales_offers.list_all() if getattr(o, "price", 0)]
        product_prices = [p.price for p in self._store.agro_products.list_all() if getattr(p, "price", 0)]
        all_prices = prices + product_prices
        avg = (sum(all_prices) / len(all_prices)) if all_prices else 0.0
        return {
            "sample_size": len(all_prices),
            "avg_price": round(avg, 2),
            "min_price": min(all_prices) if all_prices else 0.0,
            "max_price": max(all_prices) if all_prices else 0.0,
        }

    def export_analytics(self) -> dict[str, Any]:
        intl = self._store.intl_shipments.list_all()
        by_status: dict[str, int] = {}
        by_country: dict[str, int] = {}
        for s in intl:
            status = getattr(s.status, "value", str(s.status))
            by_status[status] = by_status.get(status, 0) + 1
            country = getattr(s, "destination_country", "") or "unknown"
            by_country[country] = by_country.get(country, 0) + 1
        return {
            "intl_shipments": len(intl),
            "legacy_export_shipments": self._store.export_shipments.count(),
            "by_status": by_status,
            "by_destination": by_country,
            "containers": self._store.containers.count(),
            "customs": self._store.customs_declarations.count(),
        }

    def customer_analytics(self) -> dict[str, Any]:
        return {
            "buyers": self._store.buyers.count(),
            "farmers": self._store.farmers.count(),
            "suppliers": self._store.suppliers.count(),
            "exporters": self._store.exporters.count(),
            "leads": self._store.agro_leads.count(),
        }

    def regional_analytics(self) -> dict[str, Any]:
        regions: dict[str, int] = {}
        for product in self._store.agro_products.list_all():
            region = getattr(product, "region", "") or "unknown"
            regions[region] = regions.get(region, 0) + 1
        for wh in self._store.agro_warehouses.list_all():
            region = getattr(wh, "region", "") or "unknown"
            regions[region] = regions.get(region, 0) + 1
        return {"by_region": regions, "regions": len(regions)}

    def domain_report(self, domain: str) -> dict[str, Any]:
        mapping = {
            "sales": self.sales_analytics,
            "inventory": self.inventory_analytics,
            "harvest": self.harvest_analytics,
            "crop": self.crop_analytics,
            "demand": self.demand_analytics,
            "supply": self.supply_analytics,
            "pricing": self.pricing_analytics,
            "export": self.export_analytics,
            "customer": self.customer_analytics,
            "regional": self.regional_analytics,
        }
        fn = mapping.get(domain)
        if fn is None:
            return {"error": f"unknown domain: {domain}"}
        return {"domain": domain, **fn()}


analytics_service = AnalyticsService()
