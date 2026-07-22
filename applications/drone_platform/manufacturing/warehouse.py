"""Component warehouse categories and traceability (Sprint 11.6)."""

from __future__ import annotations

from typing import Any

from applications.drone_platform.inventory.service import InventoryService, inventory_service
from applications.drone_platform.shared.store import DroneStore, drone_store
from applications.drone_platform.warehouse.service import WarehouseService


COMPONENT_CATEGORIES = (
    "electronic_components",
    "mechanical_parts",
    "motors",
    "esc",
    "gps",
    "flight_controllers",
    "sensors",
    "frames",
    "propellers",
    "batteries",
    "fasteners",
    "consumables",
)


class ComponentWarehouse(WarehouseService):
    """Extended warehouse with UAV component categories and traceability."""

    def __init__(self, inventory: InventoryService | None = None, store: DroneStore | None = None) -> None:
        super().__init__(inventory=inventory or inventory_service, store=store or drone_store)

    def categories(self) -> list[str]:
        return list(COMPONENT_CATEGORIES)

    def stock_by_category(self, category: str, *, warehouse_id: str | None = None) -> list[dict[str, Any]]:
        items = self.inventory.list_stock(warehouse_id)
        return [s.to_dict() for s in items if s.component_type == category]

    def supplier_registry(self) -> list[dict[str, Any]]:
        return [s.to_dict() for s in self.inventory.list_suppliers()]

    def stock_levels(self, *, warehouse_id: str | None = None) -> dict[str, Any]:
        items = self.inventory.list_stock(warehouse_id)
        levels = {}
        for s in items:
            levels[s.sku] = levels.get(s.sku, 0) + int(s.quantity)
        return {"warehouse_id": warehouse_id, "levels": levels, "sku_count": len(levels)}

    def reservations(self) -> list[dict[str, Any]]:
        return [r.to_dict() for r in self.store.reservations.list_all()]

    def traceability(self, *, serial_number: str) -> dict[str, Any]:
        matches = []
        for s in self.inventory.list_stock():
            if serial_number in (s.serial_numbers or []):
                matches.append(s.to_dict())
        return {"serial_number": serial_number, "stock_records": matches, "found": bool(matches)}

    def receive_components(
        self,
        *,
        warehouse_id: str,
        component_type: str,
        sku: str,
        quantity: int,
        serial_numbers: list[str] | None = None,
        batch_id: str = "",
    ) -> dict[str, Any]:
        if component_type not in COMPONENT_CATEGORIES:
            # allow custom but prefer catalog
            pass
        stock = self.inventory.add_stock(
            warehouse_id=warehouse_id,
            component_type=component_type,
            sku=sku,
            quantity=quantity,
            serial_numbers=serial_numbers,
            batch_id=batch_id,
            lifecycle_stage="received",
        )
        return stock.to_dict()

    def status(self) -> dict[str, Any]:
        return {
            "component_warehouse": "1.0",
            "categories": self.categories(),
            "warehouses": self.store.warehouses.count(),
            "stock_items": self.store.stock_items.count(),
            "suppliers": self.store.suppliers.count(),
            "capabilities": [
                "electronic_components",
                "mechanical_parts",
                "motors",
                "esc",
                "gps",
                "flight_controllers",
                "sensors",
                "frames",
                "propellers",
                "batteries",
                "fasteners",
                "consumables",
                "supplier_registry",
                "stock_levels",
                "reservations",
                "traceability",
            ],
        }


component_warehouse = ComponentWarehouse()
