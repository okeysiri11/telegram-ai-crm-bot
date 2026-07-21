# StorageService — storage lots and location occupancy.

from __future__ import annotations

from events.publisher import publish

from applications.agro_marketplace.product_catalog.events import BatchStoredEvent
from applications.agro_marketplace.product_catalog.models import StorageLotRecord
from applications.agro_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.agro_marketplace.shared.store import AgroStore, agro_store
from applications.agro_marketplace.warehouse.engine import WarehouseEngine, warehouse_engine


class StorageService:
    def __init__(
        self,
        store: AgroStore | None = None,
        warehouses: WarehouseEngine | None = None,
    ) -> None:
        self._store = store or agro_store
        self._warehouses = warehouses or warehouse_engine

    def get_lot(self, lot_id: str) -> StorageLotRecord:
        lot = self._store.storage_lot_records.get(lot_id)
        if lot is None:
            raise NotFoundError("StorageLot", lot_id)
        return lot

    def list_lots(self, *, warehouse_id: str | None = None) -> list[StorageLotRecord]:
        lots = self._store.storage_lot_records.list_all()
        if warehouse_id:
            lots = [lot for lot in lots if lot.warehouse_id == warehouse_id]
        return lots

    async def store_batch_lot(self, lot: StorageLotRecord) -> StorageLotRecord:
        if lot.quantity_tons <= 0:
            raise ValidationError("quantity_tons must be positive")
        self._warehouses.get_warehouse(lot.warehouse_id)
        if lot.location_id:
            location = self._warehouses.get_location(lot.location_id)
            if location.used_tons + lot.quantity_tons > location.capacity_tons > 0:
                raise ValidationError("insufficient location capacity")
            location.used_tons += lot.quantity_tons
            self._store.storage_locations.save(location.location_id, location)
        self._warehouses.adjust_capacity_usage(lot.warehouse_id, lot.quantity_tons)
        saved = self._store.storage_lot_records.save(lot.lot_id, lot)
        await publish(
            BatchStoredEvent(
                batch_id=saved.batch_id,
                lot_id=saved.lot_id,
                warehouse_id=saved.warehouse_id,
                quantity=saved.quantity_tons,
            )
        )
        return saved


storage_service = StorageService()
