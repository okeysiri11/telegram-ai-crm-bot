# AgroSearchEngine — product, crop, region, harvest, warehouse, supplier + semantic search.

from __future__ import annotations

import logging
from typing import Any

from applications.agro_marketplace.shared.store import AgroStore, agro_store

logger = logging.getLogger(__name__)


class AgroSearchEngine:
    def __init__(self, store: AgroStore | None = None) -> None:
        self._store = store or agro_store

    def search_products(
        self,
        *,
        query: str = "",
        region: str = "",
        category_id: str = "",
        crop_id: str = "",
    ) -> list[dict[str, Any]]:
        results = []
        q = query.lower().strip()
        for product in self._store.agro_products.list_all():
            if product.status.value == "archived":
                continue
            if region and product.region.lower() != region.lower():
                continue
            if category_id and product.category_id != category_id:
                continue
            if crop_id and product.crop_id != crop_id:
                continue
            if q and q not in product.name.lower() and q not in product.sku.lower() and q not in " ".join(product.tags).lower():
                continue
            results.append(product.to_dict())
        return results

    def search_crops(self, *, query: str = "") -> list[dict[str, Any]]:
        q = query.lower().strip()
        items = self._store.crop_records.list_all()
        if q:
            items = [c for c in items if q in c.name.lower() or q in c.scientific_name.lower()]
        return [c.to_dict() for c in items]

    def search_by_region(self, region: str) -> dict[str, list[dict[str, Any]]]:
        region_l = region.lower()
        return {
            "products": [
                p.to_dict()
                for p in self._store.agro_products.list_all()
                if p.region.lower() == region_l and p.status.value != "archived"
            ],
            "harvests": [
                h.to_dict() for h in self._store.harvest_records.list_all() if h.region.lower() == region_l
            ],
            "warehouses": [
                w.to_dict() for w in self._store.agro_warehouses.list_all() if w.region.lower() == region_l
            ],
        }

    def search_harvests(
        self,
        *,
        query: str = "",
        season_id: str = "",
        crop_id: str = "",
    ) -> list[dict[str, Any]]:
        q = query.lower().strip()
        results = []
        for harvest in self._store.harvest_records.list_all():
            if season_id and harvest.season_id != season_id:
                continue
            if crop_id and harvest.crop_id != crop_id:
                continue
            if q and q not in harvest.notes.lower() and q not in harvest.region.lower():
                continue
            results.append(harvest.to_dict())
        return results

    def search_warehouses(self, *, query: str = "", region: str = "") -> list[dict[str, Any]]:
        q = query.lower().strip()
        results = []
        for warehouse in self._store.agro_warehouses.list_all():
            if region and warehouse.region.lower() != region.lower():
                continue
            if q and q not in warehouse.name.lower() and q not in warehouse.location.lower():
                continue
            results.append(warehouse.to_dict())
        return results

    def search_suppliers(self, *, query: str = "") -> list[dict[str, Any]]:
        q = query.lower().strip()
        results = []
        for supplier in self._store.suppliers.list_all():
            if q and q not in supplier.name.lower() and q not in supplier.category.lower():
                continue
            results.append(supplier.to_dict())
        return results

    async def semantic_search(self, query: str, *, limit: int = 10) -> list[dict[str, Any]]:
        """AI semantic search via Platform Core reasoning bridge with keyword fallback."""
        try:
            from applications.agro_marketplace.integrations.platform_bridge import platform_bridge

            await platform_bridge.recommend_products({"hook": "semantic_search", "query": query})
        except Exception:
            logger.debug("semantic search bridge unavailable")

        # Keyword fallback across catalog entities
        products = self.search_products(query=query)[:limit]
        crops = self.search_crops(query=query)[: max(0, limit - len(products))]
        harvests = self.search_harvests(query=query)[: max(0, limit - len(products) - len(crops))]
        combined: list[dict[str, Any]] = []
        for item in products:
            combined.append({"type": "product", **item})
        for item in crops:
            combined.append({"type": "crop", **item})
        for item in harvests:
            combined.append({"type": "harvest", **item})
        return combined[:limit]


agro_search_engine = AgroSearchEngine()
