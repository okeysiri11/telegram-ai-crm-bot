# Warehouse Engine — receiving, storage, picking, packing, cross-dock, inventory.

from __future__ import annotations

import time

from events.publisher import publish

from applications.port_erp.operations.service import OperationsService, operations_service
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.models import Warehouse
from applications.port_erp.shared.store import PortStore, port_store
from applications.port_erp.terminal_operations.events import WarehouseUpdatedEvent
from applications.port_erp.terminal_operations.models import (
    CycleCount,
    InventoryItem,
    StockMovement,
    WarehouseOperationType,
    WarehouseTask,
    WarehouseZone,
)


class WarehouseEngine:
    def __init__(
        self,
        store: PortStore | None = None,
        operations: OperationsService | None = None,
    ) -> None:
        self._store = store or port_store
        self._operations = operations or operations_service

    def register_warehouse(self, warehouse: Warehouse) -> Warehouse:
        return self._operations.register_warehouse(warehouse)

    def list_warehouses(self, *, port_id: str | None = None) -> list[Warehouse]:
        return self._operations.list_warehouses(port_id=port_id)

    def get_warehouse(self, warehouse_id: str) -> Warehouse:
        warehouse = self._store.warehouses.get(warehouse_id)
        if warehouse is None:
            raise NotFoundError("Warehouse", warehouse_id)
        return warehouse

    def create_zone(self, zone: WarehouseZone) -> WarehouseZone:
        self.get_warehouse(zone.warehouse_id)
        if not zone.name:
            raise ValidationError("name is required")
        return self._store.warehouse_zones.save(zone.zone_id, zone)

    def list_zones(self, *, warehouse_id: str | None = None) -> list[WarehouseZone]:
        items = self._store.warehouse_zones.list_all()
        if warehouse_id:
            items = [z for z in items if z.warehouse_id == warehouse_id]
        return items

    def upsert_inventory(self, item: InventoryItem) -> InventoryItem:
        self.get_warehouse(item.warehouse_id)
        if not item.sku:
            raise ValidationError("sku is required")
        existing = next(
            (
                i
                for i in self._store.inventory_items.list_all()
                if i.warehouse_id == item.warehouse_id and i.sku == item.sku and i.zone_id == item.zone_id
            ),
            None,
        )
        if existing:
            existing.quantity = item.quantity
            existing.description = item.description or existing.description
            existing.updated_at = time.time()
            return self._store.inventory_items.save(existing.item_id, existing)
        return self._store.inventory_items.save(item.item_id, item)

    def list_inventory(self, *, warehouse_id: str | None = None) -> list[InventoryItem]:
        items = self._store.inventory_items.list_all()
        if warehouse_id:
            items = [i for i in items if i.warehouse_id == warehouse_id]
        return items

    async def move_stock(
        self,
        *,
        warehouse_id: str,
        item_id: str,
        quantity: float,
        movement_type: str = "transfer",
        from_zone_id: str = "",
        to_zone_id: str = "",
        reference: str = "",
    ) -> StockMovement:
        item = self._store.inventory_items.get(item_id)
        if item is None:
            raise NotFoundError("InventoryItem", item_id)
        if quantity <= 0:
            raise ValidationError("quantity must be positive")
        if movement_type in ("out", "pick", "ship") and item.quantity < quantity:
            raise ValidationError("insufficient stock")

        if movement_type in ("in", "receive"):
            item.quantity += quantity
        elif movement_type in ("out", "pick", "ship"):
            item.quantity -= quantity
        elif movement_type == "transfer":
            if item.quantity < quantity:
                raise ValidationError("insufficient stock")
            item.zone_id = to_zone_id or item.zone_id
        item.updated_at = time.time()
        self._store.inventory_items.save(item.item_id, item)

        movement = StockMovement(
            warehouse_id=warehouse_id,
            item_id=item_id,
            movement_type=movement_type,
            quantity=quantity,
            from_zone_id=from_zone_id,
            to_zone_id=to_zone_id,
            reference=reference,
        )
        saved = self._store.stock_movements.save(movement.movement_id, movement)
        await publish(
            WarehouseUpdatedEvent(
                warehouse_id=warehouse_id,
                operation=f"stock_{movement_type}",
                reference=reference or saved.movement_id,
            )
        )
        return saved

    def list_movements(self, *, warehouse_id: str | None = None) -> list[StockMovement]:
        items = self._store.stock_movements.list_all()
        if warehouse_id:
            items = [m for m in items if m.warehouse_id == warehouse_id]
        return items

    async def create_task(self, task: WarehouseTask) -> WarehouseTask:
        self.get_warehouse(task.warehouse_id)
        saved = self._store.warehouse_tasks.save(task.task_id, task)
        await publish(
            WarehouseUpdatedEvent(
                warehouse_id=task.warehouse_id,
                operation=task.operation.value,
                reference=task.reference or task.task_id,
            )
        )
        return saved

    async def complete_task(self, task_id: str) -> WarehouseTask:
        task = self._store.warehouse_tasks.get(task_id)
        if task is None:
            raise NotFoundError("WarehouseTask", task_id)
        task.status = "completed"
        task.completed_at = time.time()
        saved = self._store.warehouse_tasks.save(task_id, task)
        await publish(
            WarehouseUpdatedEvent(
                warehouse_id=saved.warehouse_id,
                operation=f"{saved.operation.value}_completed",
                reference=saved.reference or saved.task_id,
            )
        )
        return saved

    def list_tasks(self, *, warehouse_id: str | None = None) -> list[WarehouseTask]:
        items = self._store.warehouse_tasks.list_all()
        if warehouse_id:
            items = [t for t in items if t.warehouse_id == warehouse_id]
        return items

    async def cycle_count(self, count: CycleCount) -> CycleCount:
        self.get_warehouse(count.warehouse_id)
        count.variance = count.counted_qty - count.expected_qty
        count.status = "completed"
        saved = self._store.cycle_counts.save(count.count_id, count)
        await publish(
            WarehouseUpdatedEvent(
                warehouse_id=count.warehouse_id,
                operation=WarehouseOperationType.CYCLE_COUNT.value,
                reference=saved.count_id,
            )
        )
        return saved

    def list_cycle_counts(self, *, warehouse_id: str | None = None) -> list[CycleCount]:
        items = self._store.cycle_counts.list_all()
        if warehouse_id:
            items = [c for c in items if c.warehouse_id == warehouse_id]
        return items


warehouse_engine = WarehouseEngine()
