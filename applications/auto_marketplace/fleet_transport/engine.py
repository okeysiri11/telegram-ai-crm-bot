# Fleet Transport — dealer/auction/warehouse/port/rail movements, truck scheduling.

from __future__ import annotations

import time

from applications.auto_marketplace.shared.exceptions import ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store
from applications.auto_marketplace.transport.models import FleetMovement


class FleetTransportEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def plan(self, movement: FleetMovement) -> FleetMovement:
        if not movement.vehicle_ids:
            raise ValidationError("vehicle_ids are required")
        if not movement.from_location or not movement.to_location:
            raise ValidationError("from_location and to_location are required")
        if not movement.truck_schedule:
            movement.truck_schedule = {"departure": time.time() + 3600, "trucks": 1}
        movement.status = "planned"
        return self._store.fleet_movements.save(movement.movement_id, movement)

    def schedule_truck(self, movement_id: str, *, departure: float, trucks: int = 1) -> FleetMovement:
        item = self._store.fleet_movements.get(movement_id)
        if item is None:
            from applications.auto_marketplace.shared.exceptions import NotFoundError

            raise NotFoundError("FleetMovement", movement_id)
        item.truck_schedule = {"departure": departure, "trucks": trucks}
        item.status = "scheduled"
        return self._store.fleet_movements.save(movement_id, item)

    def list_movements(self, *, kind: str = "") -> list[FleetMovement]:
        items = self._store.fleet_movements.list_all()
        if kind:
            items = [m for m in items if m.kind == kind]
        return items

    def metrics(self) -> dict:
        return {"fleet_movements": self._store.fleet_movements.count()}


fleet_transport_engine = FleetTransportEngine()
