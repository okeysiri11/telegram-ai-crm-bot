# WarehouseEngine — multi-warehouse management and storage locations.

from __future__ import annotations

from events.publisher import publish

from applications.agro_marketplace.product_catalog.events import WarehouseCreatedEvent
from applications.agro_marketplace.product_catalog.models import AgroWarehouse, StorageLocation
from applications.agro_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.agro_marketplace.shared.models import Warehouse as LegacyWarehouse
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class WarehouseEngine:
    def __init__(self, store: AgroStore | None = None) -> None:
        self._store = store or agro_store

    def _sync_legacy(self, warehouse: AgroWarehouse) -> None:
        legacy = LegacyWarehouse(
            warehouse_id=warehouse.warehouse_id,
            name=warehouse.name,
            owner_id=warehouse.owner_id,
            location=warehouse.location or warehouse.region,
            capacity_tons=warehouse.capacity_tons,
            used_tons=warehouse.used_tons,
        )
        self._store.warehouses.save(legacy.warehouse_id, legacy)

    async def create_warehouse(self, warehouse: AgroWarehouse) -> AgroWarehouse:
        if not warehouse.name:
            raise ValidationError("name is required")
        if warehouse.capacity_tons < 0:
            raise ValidationError("capacity_tons must be non-negative")
        saved = self._store.agro_warehouses.save(warehouse.warehouse_id, warehouse)
        self._sync_legacy(saved)
        await publish(
            WarehouseCreatedEvent(
                warehouse_id=saved.warehouse_id,
                name=saved.name,
                region=saved.region,
            )
        )
        return saved

    def get_warehouse(self, warehouse_id: str) -> AgroWarehouse:
        warehouse = self._store.agro_warehouses.get(warehouse_id)
        if warehouse is None:
            raise NotFoundError("Warehouse", warehouse_id)
        return warehouse

    def list_warehouses(self, *, region: str | None = None, active_only: bool = True) -> list[AgroWarehouse]:
        items = self._store.agro_warehouses.list_all()
        if active_only:
            items = [w for w in items if w.is_active]
        if region:
            items = [w for w in items if w.region.lower() == region.lower()]
        return items

    def create_location(self, location: StorageLocation) -> StorageLocation:
        self.get_warehouse(location.warehouse_id)
        return self._store.storage_locations.save(location.location_id, location)

    def list_locations(self, *, warehouse_id: str | None = None) -> list[StorageLocation]:
        items = self._store.storage_locations.list_all()
        if warehouse_id:
            items = [loc for loc in items if loc.warehouse_id == warehouse_id]
        return items

    def get_location(self, location_id: str) -> StorageLocation:
        location = self._store.storage_locations.get(location_id)
        if location is None:
            raise NotFoundError("StorageLocation", location_id)
        return location

    def adjust_capacity_usage(self, warehouse_id: str, delta_tons: float) -> AgroWarehouse:
        warehouse = self.get_warehouse(warehouse_id)
        new_used = warehouse.used_tons + delta_tons
        if new_used < 0:
            new_used = 0.0
        if new_used > warehouse.capacity_tons:
            raise ValidationError("insufficient warehouse capacity")
        warehouse.used_tons = new_used
        saved = self._store.agro_warehouses.save(warehouse_id, warehouse)
        self._sync_legacy(saved)
        return saved


warehouse_engine = WarehouseEngine()
