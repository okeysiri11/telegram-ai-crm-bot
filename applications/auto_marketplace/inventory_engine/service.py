# Inventory engine — stock, warehouse, and dealer inventory management.

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from events.publisher import publish
from applications.auto_marketplace.shared.exceptions import NotFoundError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store
from applications.auto_marketplace.specifications.models import InventoryVehicleStatus
from applications.auto_marketplace.vehicle_catalog.events import (
    InventoryChangedEvent,
    VehicleReservedEvent,
    VehicleSoldEvent,
)
from applications.auto_marketplace.vehicle_catalog.models import CatalogVehicle
from applications.auto_marketplace.vehicle_catalog.service import VehicleCatalogService, vehicle_catalog_service


@dataclass
class Warehouse:
    warehouse_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    city: str = ""
    capacity: int = 100

    def to_dict(self) -> dict[str, Any]:
        return {
            "warehouse_id": self.warehouse_id,
            "name": self.name,
            "city": self.city,
            "capacity": self.capacity,
        }


class InventoryEngine:
    def __init__(
        self,
        store: MarketplaceStore | None = None,
        catalog: VehicleCatalogService | None = None,
    ) -> None:
        self._store = store or marketplace_store
        self._catalog = catalog or vehicle_catalog_service

    def create_warehouse(self, warehouse: Warehouse) -> Warehouse:
        return self._store.warehouses.save(warehouse.warehouse_id, warehouse)

    def list_warehouses(self) -> list[Warehouse]:
        return self._store.warehouses.list_all()

    def _get_catalog_vehicle(self, vehicle_id: str) -> CatalogVehicle:
        return self._catalog.get(vehicle_id)

    async def mark_incoming(self, vehicle_id: str, *, warehouse_id: str = "") -> CatalogVehicle:
        updates: dict[str, Any] = {"status": InventoryVehicleStatus.INCOMING}
        if warehouse_id:
            updates["warehouse_id"] = warehouse_id
        vehicle = await self._catalog.update(vehicle_id, **updates)
        await publish(
            InventoryChangedEvent(
                warehouse_id=warehouse_id,
                dealer_id=vehicle.dealer_id,
                change_type="incoming",
                count_delta=1,
            )
        )
        return vehicle

    async def mark_available(self, vehicle_id: str) -> CatalogVehicle:
        return await self._catalog.update(vehicle_id, status=InventoryVehicleStatus.AVAILABLE)

    async def mark_listed(self, vehicle_id: str) -> CatalogVehicle:
        return await self._catalog.update(vehicle_id, status=InventoryVehicleStatus.LISTED)

    async def reserve(
        self,
        vehicle_id: str,
        *,
        reservation_id: str,
        customer_id: str,
    ) -> CatalogVehicle:
        vehicle = await self._catalog.update(vehicle_id, status=InventoryVehicleStatus.RESERVED)
        await publish(
            VehicleReservedEvent(
                vehicle_id=vehicle_id,
                reservation_id=reservation_id,
                customer_id=customer_id,
            )
        )
        await publish(
            InventoryChangedEvent(
                warehouse_id=vehicle.warehouse_id,
                dealer_id=vehicle.dealer_id,
                change_type="reserved",
                count_delta=0,
            )
        )
        return vehicle

    async def mark_sold(self, vehicle_id: str, *, deal_id: str = "", final_price: float = 0.0) -> CatalogVehicle:
        vehicle = await self._catalog.update(vehicle_id, status=InventoryVehicleStatus.SOLD)
        await publish(
            VehicleSoldEvent(vehicle_id=vehicle_id, deal_id=deal_id, final_price=final_price)
        )
        await publish(
            InventoryChangedEvent(
                warehouse_id=vehicle.warehouse_id,
                dealer_id=vehicle.dealer_id,
                change_type="sold",
                count_delta=-1,
            )
        )
        return vehicle

    async def mark_outgoing(self, vehicle_id: str) -> CatalogVehicle:
        return await self._catalog.update(vehicle_id, status=InventoryVehicleStatus.OUTGOING)

    def availability(self, *, dealer_id: str | None = None, warehouse_id: str | None = None) -> dict[str, Any]:
        vehicles = self._catalog.list_vehicles(dealer_id=dealer_id)
        if warehouse_id:
            vehicles = [v for v in vehicles if v.warehouse_id == warehouse_id]
        available = [v for v in vehicles if v.status in {
            InventoryVehicleStatus.AVAILABLE,
            InventoryVehicleStatus.LISTED,
        }]
        return {
            "total": len(vehicles),
            "available": len(available),
            "reserved": sum(1 for v in vehicles if v.status == InventoryVehicleStatus.RESERVED),
            "sold": sum(1 for v in vehicles if v.status == InventoryVehicleStatus.SOLD),
            "incoming": sum(1 for v in vehicles if v.status == InventoryVehicleStatus.INCOMING),
            "outgoing": sum(1 for v in vehicles if v.status == InventoryVehicleStatus.OUTGOING),
        }

    def dealer_inventory(self, dealer_id: str) -> list[CatalogVehicle]:
        return self._catalog.list_vehicles(dealer_id=dealer_id)

    def warehouse_inventory(self, warehouse_id: str) -> list[CatalogVehicle]:
        return [v for v in self._catalog.list_vehicles(include_archived=True) if v.warehouse_id == warehouse_id]

    def stock_summary(self) -> dict[str, Any]:
        vehicles = self._catalog.list_vehicles(include_archived=True)
        by_status: dict[str, int] = {}
        for v in vehicles:
            by_status[v.status.value] = by_status.get(v.status.value, 0) + 1
        return {"total": len(vehicles), "by_status": by_status, "warehouses": self._store.warehouses.count()}


inventory_engine = InventoryEngine()
