# CatalogService — vehicle catalog management (Sprint 10.1 categories).

from __future__ import annotations

import time

from applications.auto_marketplace.foundation.models import CatalogCategory
from applications.auto_marketplace.shared.exceptions import NotFoundError
from applications.auto_marketplace.shared.models import Vehicle, VehicleStatus
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class CatalogService:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def categories(self) -> list[str]:
        return [c.value for c in CatalogCategory]

    def list_vehicles(
        self,
        *,
        status: VehicleStatus | None = None,
        category: str | None = None,
    ) -> list[Vehicle]:
        items = self._store.vehicles.list_all()
        if status:
            items = [v for v in items if v.status == status]
        if category:
            cat = category.lower()
            filtered = []
            for v in items:
                meta_cat = str(getattr(v, "category", "") or "").lower()
                hay = f"{meta_cat} {v.description} {' '.join(v.features)} {v.specification.body_type}".lower()
                if cat == meta_cat or cat in hay:
                    filtered.append(v)
            items = filtered
        return items

    def get_vehicle(self, vehicle_id: str) -> Vehicle:
        vehicle = self._store.vehicles.get(vehicle_id)
        if vehicle is None:
            raise NotFoundError("Vehicle", vehicle_id)
        return vehicle

    def create_vehicle(self, vehicle: Vehicle, *, category: str | None = None) -> Vehicle:
        if category:
            setattr(vehicle, "category", category)
        vehicle.updated_at = time.time()
        return self._store.vehicles.save(vehicle.vehicle_id, vehicle)

    def update_vehicle(self, vehicle_id: str, **updates: object) -> Vehicle:
        vehicle = self.get_vehicle(vehicle_id)
        for key, value in updates.items():
            if hasattr(vehicle, key) and value is not None:
                setattr(vehicle, key, value)
            elif key == "category" and value is not None:
                setattr(vehicle, "category", value)
        vehicle.updated_at = time.time()
        return self._store.vehicles.save(vehicle_id, vehicle)

    def publish_vehicle(self, vehicle_id: str) -> Vehicle:
        return self.update_vehicle(vehicle_id, status=VehicleStatus.LISTED)

    def overview(self) -> dict:
        by_category: dict[str, int] = {c.value: 0 for c in CatalogCategory}
        for vehicle in self._store.vehicles.list_all():
            cat = str(getattr(vehicle, "category", "") or CatalogCategory.CARS.value)
            by_category[cat] = by_category.get(cat, 0) + 1
        return {
            "total": self._store.vehicles.count(),
            "categories": self.categories(),
            "by_category": by_category,
        }


catalog_service = CatalogService()
