# InventoryEngine — stock levels, movements, transfers, shipments.

from __future__ import annotations

import time

from events.publisher import publish

from applications.agro_marketplace.product_catalog.events import InventoryUpdatedEvent, ShipmentPreparedEvent
from applications.agro_marketplace.product_catalog.models import (
    AvailabilityStatus,
    InventoryItem,
    InventoryMovement,
    MovementType,
    UnitOfMeasure,
)
from applications.agro_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.agro_marketplace.shared.store import AgroStore, agro_store
from applications.agro_marketplace.storage.service import StorageService, storage_service
from applications.agro_marketplace.warehouse.engine import WarehouseEngine, warehouse_engine


class InventoryEngine:
    def __init__(
        self,
        store: AgroStore | None = None,
        warehouses: WarehouseEngine | None = None,
        storage: StorageService | None = None,
    ) -> None:
        self._store = store or agro_store
        self._warehouses = warehouses or warehouse_engine
        self._storage = storage or storage_service

    def get_item(self, item_id: str) -> InventoryItem:
        item = self._store.inventory_items.get(item_id)
        if item is None:
            raise NotFoundError("InventoryItem", item_id)
        return item

    def list_items(
        self,
        *,
        warehouse_id: str | None = None,
        product_id: str | None = None,
    ) -> list[InventoryItem]:
        items = self._store.inventory_items.list_all()
        if warehouse_id:
            items = [i for i in items if i.warehouse_id == warehouse_id]
        if product_id:
            items = [i for i in items if i.product_id == product_id]
        return items

    def _find_or_create_item(
        self,
        *,
        product_id: str,
        warehouse_id: str,
        location_id: str = "",
        lot_id: str = "",
        batch_id: str = "",
        uom: UnitOfMeasure = UnitOfMeasure.TON,
    ) -> InventoryItem:
        for item in self.list_items(warehouse_id=warehouse_id, product_id=product_id):
            if item.location_id == location_id and item.lot_id == lot_id:
                return item
        item = InventoryItem(
            product_id=product_id,
            warehouse_id=warehouse_id,
            location_id=location_id,
            lot_id=lot_id,
            batch_id=batch_id,
            uom=uom,
            status=AvailabilityStatus.AVAILABLE,
        )
        return self._store.inventory_items.save(item.item_id, item)

    async def _record_movement(self, movement: InventoryMovement) -> InventoryMovement:
        return self._store.inventory_movements.save(movement.movement_id, movement)

    async def incoming_harvest(
        self,
        *,
        product_id: str,
        warehouse_id: str,
        quantity: float,
        location_id: str = "",
        lot_id: str = "",
        batch_id: str = "",
        uom: UnitOfMeasure = UnitOfMeasure.TON,
        reference: str = "",
    ) -> InventoryItem:
        if quantity <= 0:
            raise ValidationError("quantity must be positive")
        self._warehouses.get_warehouse(warehouse_id)
        item = self._find_or_create_item(
            product_id=product_id,
            warehouse_id=warehouse_id,
            location_id=location_id,
            lot_id=lot_id,
            batch_id=batch_id,
            uom=uom,
        )
        item.quantity += quantity
        item.updated_at = time.time()
        saved = self._store.inventory_items.save(item.item_id, item)
        self._warehouses.adjust_capacity_usage(warehouse_id, quantity)
        movement = InventoryMovement(
            movement_type=MovementType.INCOMING,
            product_id=product_id,
            quantity=quantity,
            uom=uom,
            to_warehouse_id=warehouse_id,
            to_location_id=location_id,
            lot_id=lot_id,
            batch_id=batch_id,
            reference=reference or "incoming_harvest",
        )
        await self._record_movement(movement)
        await publish(
            InventoryUpdatedEvent(
                item_id=saved.item_id,
                product_id=product_id,
                warehouse_id=warehouse_id,
                quantity=saved.quantity,
                change_type="incoming",
            )
        )
        return saved

    async def prepare_shipment(
        self,
        *,
        product_id: str,
        warehouse_id: str,
        quantity: float,
        reference: str = "",
        location_id: str = "",
    ) -> InventoryMovement:
        if quantity <= 0:
            raise ValidationError("quantity must be positive")
        item = self._find_or_create_item(
            product_id=product_id,
            warehouse_id=warehouse_id,
            location_id=location_id,
        )
        if item.available_quantity < quantity:
            raise ValidationError("insufficient available inventory")
        item.quantity -= quantity
        item.updated_at = time.time()
        self._store.inventory_items.save(item.item_id, item)
        self._warehouses.adjust_capacity_usage(warehouse_id, -quantity)
        movement = InventoryMovement(
            movement_type=MovementType.OUTGOING,
            product_id=product_id,
            quantity=quantity,
            from_warehouse_id=warehouse_id,
            from_location_id=location_id,
            reference=reference or "shipment",
        )
        saved = await self._record_movement(movement)
        await publish(
            InventoryUpdatedEvent(
                item_id=item.item_id,
                product_id=product_id,
                warehouse_id=warehouse_id,
                quantity=item.quantity,
                change_type="outgoing",
            )
        )
        await publish(
            ShipmentPreparedEvent(
                movement_id=saved.movement_id,
                warehouse_id=warehouse_id,
                product_id=product_id,
                quantity=quantity,
                reference=saved.reference,
            )
        )
        return saved

    async def transfer(
        self,
        *,
        product_id: str,
        from_warehouse_id: str,
        to_warehouse_id: str,
        quantity: float,
        from_location_id: str = "",
        to_location_id: str = "",
    ) -> InventoryMovement:
        if from_warehouse_id == to_warehouse_id:
            raise ValidationError("source and destination warehouses must differ")
        await self.prepare_shipment(
            product_id=product_id,
            warehouse_id=from_warehouse_id,
            quantity=quantity,
            location_id=from_location_id,
            reference="transfer_out",
        )
        await self.incoming_harvest(
            product_id=product_id,
            warehouse_id=to_warehouse_id,
            quantity=quantity,
            location_id=to_location_id,
            reference="transfer_in",
        )
        movement = InventoryMovement(
            movement_type=MovementType.TRANSFER,
            product_id=product_id,
            quantity=quantity,
            from_warehouse_id=from_warehouse_id,
            to_warehouse_id=to_warehouse_id,
            from_location_id=from_location_id,
            to_location_id=to_location_id,
            reference="stock_transfer",
        )
        return await self._record_movement(movement)

    def list_movements(self) -> list[InventoryMovement]:
        return self._store.inventory_movements.list_all()

    def availability(self, *, product_id: str = "", warehouse_id: str = "") -> dict:
        items = self.list_items(warehouse_id=warehouse_id or None, product_id=product_id or None)
        total = sum(i.quantity for i in items)
        reserved = sum(i.reserved_quantity for i in items)
        return {
            "product_id": product_id,
            "warehouse_id": warehouse_id,
            "total_quantity": total,
            "reserved_quantity": reserved,
            "available_quantity": total - reserved,
            "items": [i.to_dict() for i in items],
        }


inventory_engine = InventoryEngine()
