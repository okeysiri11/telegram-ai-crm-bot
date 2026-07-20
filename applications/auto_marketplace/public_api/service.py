# Public API — unauthenticated vehicle search and catalog access.

from __future__ import annotations

from typing import Any

from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class PublicAPIService:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def search(self, *, query: str = "", limit: int = 20) -> list[dict]:
        vehicles = self._store.catalog_vehicles.list_all() or self._store.vehicles.list_all()
        results = []
        q = query.lower()
        for v in vehicles:
            if q:
                text = f"{getattr(v, 'brand', '')} {getattr(v, 'model', '')} {getattr(v, 'description', '')}".lower()
                if q not in text:
                    continue
            results.append(v.to_dict() if hasattr(v, "to_dict") else {"vehicle_id": getattr(v, "vehicle_id", "")})
            if len(results) >= limit:
                break
        return results

    def get_vehicle(self, vehicle_id: str) -> dict | None:
        v = self._store.catalog_vehicles.get(vehicle_id) or self._store.vehicles.get(vehicle_id)
        return v.to_dict() if v and hasattr(v, "to_dict") else None

    def catalog_stats(self) -> dict[str, Any]:
        vehicles = self._store.catalog_vehicles.list_all() or self._store.vehicles.list_all()
        return {"total_vehicles": len(vehicles), "dealers": self._store.dealers.count()}


public_api_service = PublicAPIService()
