# Mobile API — mobile-optimized endpoints.

from __future__ import annotations

from typing import Any

from applications.auto_marketplace.pricing.service import recommendation_service
from applications.auto_marketplace.search.service import search_service


class MobileApi:
    def home_feed(self, *, limit: int = 10) -> dict[str, Any]:
        vehicles = search_service.search_vehicles(limit=limit)
        return {"featured": vehicles, "count": len(vehicles)}

    def recommendations(self, customer_id: str) -> dict[str, Any]:
        return {"items": recommendation_service.recommend_for_customer(customer_id)}


mobile_api = MobileApi()
