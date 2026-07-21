# WarehouseService — warehouses and storage lots.

from __future__ import annotations

from applications.agro_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.agro_marketplace.shared.models import StorageLot, Warehouse
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class WarehouseService:
    def __init__(self, store: AgroStore | None = None) -> None:
        self._store = store or agro_store

    def list_warehouses(self) -> list[Warehouse]:
        return self._store.warehouses.list_all()

    def get_warehouse(self, warehouse_id: str) -> Warehouse:
        warehouse = self._store.warehouses.get(warehouse_id)
        if warehouse is None:
            raise NotFoundError("Warehouse", warehouse_id)
        return warehouse

    def create_warehouse(self, warehouse: Warehouse) -> Warehouse:
        if warehouse.capacity_tons < 0:
            raise ValidationError("capacity_tons must be non-negative")
        return self._store.warehouses.save(warehouse.warehouse_id, warehouse)

    def store_lot(self, lot: StorageLot) -> StorageLot:
        warehouse = self.get_warehouse(lot.warehouse_id)
        if warehouse.used_tons + lot.quantity_tons > warehouse.capacity_tons:
            raise ValidationError("insufficient warehouse capacity")
        warehouse.used_tons += lot.quantity_tons
        self._store.warehouses.save(warehouse.warehouse_id, warehouse)
        return self._store.storage_lots.save(lot.lot_id, lot)

    def list_lots(self, *, warehouse_id: str | None = None) -> list[StorageLot]:
        lots = self._store.storage_lots.list_all()
        if warehouse_id:
            lots = [lot for lot in lots if lot.warehouse_id == warehouse_id]
        return lots


warehouse_service = WarehouseService()
