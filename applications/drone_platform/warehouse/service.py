from __future__ import annotations

from applications.drone_platform.inventory.service import InventoryService, inventory_service
from applications.drone_platform.shared.store import DroneStore, drone_store


class WarehouseService:
    """Thin facade over inventory warehouses for package layout completeness."""

    def __init__(self, inventory: InventoryService | None = None, store: DroneStore | None = None) -> None:
        self.inventory = inventory or inventory_service
        self.store = store or drone_store

    def create(self, *, name: str, location: str = ""):
        return self.inventory.create_warehouse(name=name, location=location)

    def list(self):
        return self.inventory.list_warehouses()


warehouse_service = WarehouseService()
