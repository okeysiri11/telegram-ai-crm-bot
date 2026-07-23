"""Shared store — Port Enterprise (Sprint 15.0)."""

from __future__ import annotations

from typing import Generic, TypeVar

T = TypeVar("T")


class EntityStore(Generic[T]):
    def __init__(self) -> None:
        self._items: dict[str, T] = {}

    def save(self, key: str, item: T) -> T:
        self._items[key] = item
        return item

    def get(self, key: str) -> T | None:
        return self._items.get(key)

    def delete(self, key: str) -> None:
        self._items.pop(key, None)

    def list_all(self) -> list[T]:
        return list(self._items.values())

    def count(self) -> int:
        return len(self._items)

    def reset(self) -> None:
        self._items.clear()


class PortEnterpriseStore:
    def __init__(self) -> None:
        # Port registry
        self.ports: EntityStore = EntityStore()
        self.terminals: EntityStore = EntityStore()
        self.docks: EntityStore = EntityStore()
        self.berths: EntityStore = EntityStore()
        self.warehouses: EntityStore = EntityStore()
        self.yards: EntityStore = EntityStore()
        self.equipment: EntityStore = EntityStore()
        # Terminal utilization
        self.terminal_capacity: EntityStore = EntityStore()
        # Cargo
        self.cargo: EntityStore = EntityStore()
        self.cargo_events: EntityStore = EntityStore()
        # Shipping companies
        self.shipping_lines: EntityStore = EntityStore()
        self.carriers: EntityStore = EntityStore()
        self.vessel_operators: EntityStore = EntityStore()
        self.agencies: EntityStore = EntityStore()
        self.service_providers: EntityStore = EntityStore()
        # Fleet
        self.vessels: EntityStore = EntityStore()
        # Operations
        self.arrivals: EntityStore = EntityStore()
        self.departures: EntityStore = EntityStore()
        self.dock_schedules: EntityStore = EntityStore()
        self.berth_allocations: EntityStore = EntityStore()
        self.load_queues: EntityStore = EntityStore()
        self.unload_queues: EntityStore = EntityStore()
        # Knowledge & dashboards
        self.knowledge: EntityStore = EntityStore()
        self.dashboards: EntityStore = EntityStore()

    def reset(self) -> None:
        for attr in vars(self).values():
            if isinstance(attr, EntityStore):
                attr.reset()


port_enterprise_store = PortEnterpriseStore()
