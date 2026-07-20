# CatalogService — vehicle catalog management.

from __future__ import annotations

import time

from applications.auto_marketplace.shared.exceptions import NotFoundError
from applications.auto_marketplace.shared.models import Vehicle, VehicleStatus
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class CatalogService:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def list_vehicles(self, *, status: VehicleStatus | None = None) -> list[Vehicle]:
        items = self._store.vehicles.list_all()
        if status:
            items = [v for v in items if v.status == status]
        return items

    def get_vehicle(self, vehicle_id: str) -> Vehicle:
        vehicle = self._store.vehicles.get(vehicle_id)
        if vehicle is None:
            raise NotFoundError("Vehicle", vehicle_id)
        return vehicle

    def create_vehicle(self, vehicle: Vehicle) -> Vehicle:
        vehicle.updated_at = time.time()
        return self._store.vehicles.save(vehicle.vehicle_id, vehicle)

    def update_vehicle(self, vehicle_id: str, **updates: object) -> Vehicle:
        vehicle = self.get_vehicle(vehicle_id)
        for key, value in updates.items():
            if hasattr(vehicle, key) and value is not None:
                setattr(vehicle, key, value)
        vehicle.updated_at = time.time()
        return self._store.vehicles.save(vehicle_id, vehicle)

    def publish_vehicle(self, vehicle_id: str) -> Vehicle:
        return self.update_vehicle(vehicle_id, status=VehicleStatus.LISTED)


catalog_service = CatalogService()
