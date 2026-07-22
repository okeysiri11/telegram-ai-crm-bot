# In-memory entity store for Port ERP.

from __future__ import annotations

from typing import Generic, TypeVar

T = TypeVar("T")


class EntityStore(Generic[T]):
    def __init__(self) -> None:
        self._items: dict[str, T] = {}

    def reset(self) -> None:
        self._items.clear()

    def save(self, entity_id: str, entity: T) -> T:
        self._items[entity_id] = entity
        return entity

    def get(self, entity_id: str) -> T | None:
        return self._items.get(entity_id)

    def delete(self, entity_id: str) -> bool:
        return self._items.pop(entity_id, None) is not None

    def list_all(self) -> list[T]:
        return list(self._items.values())

    def count(self) -> int:
        return len(self._items)


class PortStore:
    """Central in-memory persistence for Port ERP."""

    def __init__(self) -> None:
        self.ports: EntityStore = EntityStore()
        self.terminals: EntityStore = EntityStore()
        self.berths: EntityStore = EntityStore()
        self.vessels: EntityStore = EntityStore()
        self.voyages: EntityStore = EntityStore()
        self.containers: EntityStore = EntityStore()
        self.cargo: EntityStore = EntityStore()
        self.warehouses: EntityStore = EntityStore()
        self.gates: EntityStore = EntityStore()
        self.carriers: EntityStore = EntityStore()
        self.shipping_lines: EntityStore = EntityStore()
        self.customers: EntityStore = EntityStore()
        self.forwarders: EntityStore = EntityStore()
        self.customs_brokers: EntityStore = EntityStore()
        self.port_operators: EntityStore = EntityStore()
        self.documents: EntityStore = EntityStore()
        self.invoices: EntityStore = EntityStore()
        self.operations: EntityStore = EntityStore()
        # Sprint 9.2 — tracking
        self.live_positions: EntityStore = EntityStore()
        self.route_histories: EntityStore = EntityStore()
        self.geofences: EntityStore = EntityStore()
        self.timeline_events: EntityStore = EntityStore()
        self.eta_predictions: EntityStore = EntityStore()
        self.truck_tracks: EntityStore = EntityStore()
        self.container_lifecycle: EntityStore = EntityStore()
        self.geofence_occupancy: EntityStore = EntityStore()
        # Sprint 9.3 — terminal / yard / warehouse / gate / equipment / planning
        self.yard_blocks: EntityStore = EntityStore()
        self.yard_slots: EntityStore = EntityStore()
        self.yard_relocations: EntityStore = EntityStore()
        self.warehouse_zones: EntityStore = EntityStore()
        self.inventory_items: EntityStore = EntityStore()
        self.stock_movements: EntityStore = EntityStore()
        self.warehouse_tasks: EntityStore = EntityStore()
        self.cycle_counts: EntityStore = EntityStore()
        self.gate_appointments: EntityStore = EntityStore()
        self.gate_visits: EntityStore = EntityStore()
        self.equipment: EntityStore = EntityStore()
        self.crane_assignments: EntityStore = EntityStore()
        self.dispatch_jobs: EntityStore = EntityStore()
        self.terminal_plans: EntityStore = EntityStore()

    def reset(self) -> None:
        for attr in vars(self).values():
            if isinstance(attr, EntityStore):
                attr.reset()


port_store = PortStore()
