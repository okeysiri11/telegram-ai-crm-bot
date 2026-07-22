# SearchService — vehicle and dealer search (Sprint 10.1 filters).

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
        brand: str = "",
        model: str = "",
        year: int | None = None,
        min_year: int | None = None,
        max_year: int | None = None,
        mileage_max: int | None = None,
        fuel: str = "",
        transmission: str = "",
        body: str = "",
        region: str = "",
        vin: str = "",
        condition: str = "",
        min_price: float | None = None,
        max_price: float | None = None,
        status: VehicleStatus | None = VehicleStatus.LISTED,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        q = query.lower()
        brand_or_make = (brand or make).lower()
        for vehicle in self._store.vehicles.list_all():
            if status and vehicle.status != status:
                continue
            spec = vehicle.specification
            if brand_or_make and spec.make.lower() != brand_or_make:
                continue
            if model and model.lower() not in spec.model.lower():
                continue
            if year is not None and spec.year != year:
                continue
            if min_price is not None and vehicle.price < min_price:
                continue
            if max_price is not None and vehicle.price > max_price:
                continue
            if min_year is not None and spec.year < min_year:
                continue
            if max_year is not None and spec.year > max_year:
                continue
            if mileage_max is not None and spec.mileage_km > mileage_max:
                continue
            if fuel and fuel.lower() not in (spec.fuel_type or "").lower():
                continue
            if transmission and transmission.lower() not in (spec.transmission or "").lower():
                continue
            if body and body.lower() not in (spec.body_type or "").lower():
                continue
            if vin and vin.lower() not in (spec.vin or "").lower():
                continue
            if condition:
                vcond = str(getattr(vehicle, "condition", "") or "").lower()
                if condition.lower() not in vcond and condition.lower() not in (vehicle.description or "").lower():
                    continue
            if region:
                dealer = self._store.dealers.get(vehicle.dealer_id) if vehicle.dealer_id else None
                dealer_region = ""
                if dealer is not None:
                    dealer_region = " ".join(
                        [
                            getattr(dealer, "city", "") or "",
                            getattr(dealer, "region", "") or "",
                            " ".join(b.city for b in getattr(dealer, "branches", []) or []),
                        ]
                    ).lower()
                if region.lower() not in dealer_region and region.lower() not in (vehicle.description or "").lower():
                    continue
            if q:
                haystack = f"{spec.make} {spec.model} {vehicle.description} {spec.vin}".lower()
                if q not in haystack:
                    continue
            payload = vehicle.to_dict()
            payload["category"] = getattr(vehicle, "category", None)
            results.append(payload)
            if len(results) >= limit:
                break
        return results

    def search_dealers(self, *, query: str = "", limit: int = 20) -> list[dict]:
        q = query.lower()
        results = []
        for dealer in self._store.dealers.list_all():
            if q and q not in f"{dealer.name} {getattr(dealer, 'city', '')}".lower():
                if q not in dealer.name.lower():
                    continue
            results.append(dealer.to_dict())
            if len(results) >= limit:
                break
        return results

    def filter_keys(self) -> list[str]:
        return [
            "brand",
            "model",
            "year",
            "mileage",
            "fuel",
            "transmission",
            "body",
            "region",
            "price",
            "vin",
            "condition",
        ]


search_service = SearchService()
