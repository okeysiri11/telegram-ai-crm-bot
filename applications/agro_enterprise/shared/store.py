"""Shared store — Agro Enterprise (Sprint 14.0)."""

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


class AgroEnterpriseStore:
    def __init__(self) -> None:
        # Marketplace
        self.listings: EntityStore = EntityStore()
        self.orders: EntityStore = EntityStore()
        self.suppliers: EntityStore = EntityStore()
        self.buyers: EntityStore = EntityStore()
        # Farm registry
        self.farms: EntityStore = EntityStore()
        self.companies: EntityStore = EntityStore()
        self.farmland: EntityStore = EntityStore()
        self.storage: EntityStore = EntityStore()
        self.equipment: EntityStore = EntityStore()
        self.livestock: EntityStore = EntityStore()
        self.certifications: EntityStore = EntityStore()
        # Crops
        self.crops: EntityStore = EntityStore()
        self.seasons: EntityStore = EntityStore()
        self.rotations: EntityStore = EntityStore()
        self.field_assignments: EntityStore = EntityStore()
        self.yield_plans: EntityStore = EntityStore()
        self.harvest_plans: EntityStore = EntityStore()
        self.production_calendar: EntityStore = EntityStore()
        # CRM
        self.crm_contacts: EntityStore = EntityStore()
        self.contracts: EntityStore = EntityStore()
        self.leads: EntityStore = EntityStore()
        self.tasks: EntityStore = EntityStore()
        self.calendar_events: EntityStore = EntityStore()
        # Knowledge & dashboards
        self.knowledge: EntityStore = EntityStore()
        self.dashboards: EntityStore = EntityStore()

    def reset(self) -> None:
        for attr in vars(self).values():
            if isinstance(attr, EntityStore):
                attr.reset()


agro_enterprise_store = AgroEnterpriseStore()
