# SearchService — vehicle and dealer search.

from __future__ import annotations

from typing import Any

from applications.auto_marketplace.shared.models import VehicleStatus
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class SearchService:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def search_vehicles(
        self,
        *,
        query: str = "",
        make: str = "",
        model: str = "",
        min_price: float | None = None,
        max_price: float | None = None,
        min_year: int | None = None,
        max_year: int | None = None,
        status: VehicleStatus | None = VehicleStatus.LISTED,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        results = []
        q = query.lower()
        for vehicle in self._store.vehicles.list_all():
            if status and vehicle.status != status:
                continue
            spec = vehicle.specification
            if make and spec.make.lower() != make.lower():
                continue
            if model and model.lower() not in spec.model.lower():
                continue
            if min_price is not None and vehicle.price < min_price:
                continue
            if max_price is not None and vehicle.price > max_price:
                continue
            if min_year is not None and spec.year < min_year:
                continue
            if max_year is not None and spec.year > max_year:
                continue
            if q:
                haystack = f"{spec.make} {spec.model} {vehicle.description}".lower()
                if q not in haystack:
                    continue
            results.append(vehicle.to_dict())
            if len(results) >= limit:
                break
        return results

    def search_dealers(self, *, query: str = "", limit: int = 20) -> list[dict]:
        q = query.lower()
        results = []
        for dealer in self._store.dealers.list_all():
            if q and q not in f"{dealer.name} {dealer.city if hasattr(dealer, 'city') else ''}".lower():
                if q not in dealer.name.lower():
                    continue
            results.append(dealer.to_dict())
            if len(results) >= limit:
                break
        return results


search_service = SearchService()
