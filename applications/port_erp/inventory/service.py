# Inventory service — thin facade over warehouse inventory.

from __future__ import annotations

from applications.port_erp.terminal_operations.models import InventoryItem, StockMovement
from applications.port_erp.warehouse_management.engine import WarehouseEngine, warehouse_engine


class InventoryService:
    def __init__(self, warehouse: WarehouseEngine | None = None) -> None:
        self._warehouse = warehouse or warehouse_engine

    def upsert(self, item: InventoryItem) -> InventoryItem:
        return self._warehouse.upsert_inventory(item)

    def list_items(self, *, warehouse_id: str | None = None) -> list[InventoryItem]:
        return self._warehouse.list_inventory(warehouse_id=warehouse_id)

    async def move(self, **kwargs) -> StockMovement:
        return await self._warehouse.move_stock(**kwargs)

    def movements(self, *, warehouse_id: str | None = None) -> list[StockMovement]:
        return self._warehouse.list_movements(warehouse_id=warehouse_id)


inventory_service = InventoryService()
