# In-memory entity store for Drone Platform foundation.

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


class DroneStore:
    def __init__(self) -> None:
        self.components: EntityStore = EntityStore()
        self.uavs: EntityStore = EntityStore()
        self.projects: EntityStore = EntityStore()
        self.project_versions: EntityStore = EntityStore()
        self.firmware_projects: EntityStore = EntityStore()
        self.parameter_sets: EntityStore = EntityStore()
        self.parameter_templates: EntityStore = EntityStore()
        self.firmware_backups: EntityStore = EntityStore()
        self.missions: EntityStore = EntityStore()
        self.telemetry_sessions: EntityStore = EntityStore()
        self.warehouses: EntityStore = EntityStore()
        self.suppliers: EntityStore = EntityStore()
        self.stock_items: EntityStore = EntityStore()
        self.purchase_orders: EntityStore = EntityStore()
        self.reservations: EntityStore = EntityStore()
        self.documents: EntityStore = EntityStore()
        self.ai_sessions: EntityStore = EntityStore()
        self.manufacturing_builds: EntityStore = EntityStore()
        self.simulations: EntityStore = EntityStore()

    def reset(self) -> None:
        for attr in vars(self).values():
            if isinstance(attr, EntityStore):
                attr.reset()


drone_store = DroneStore()
