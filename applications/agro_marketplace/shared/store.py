# In-memory entity store for Agro Marketplace.

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


class AgroStore:
    """Central in-memory persistence for Sprint 8.1 foundation."""

    def __init__(self) -> None:
        self.farmers: EntityStore = EntityStore()
        self.farms: EntityStore = EntityStore()
        self.fields: EntityStore = EntityStore()
        self.warehouses: EntityStore = EntityStore()
        self.suppliers: EntityStore = EntityStore()
        self.buyers: EntityStore = EntityStore()
        self.products: EntityStore = EntityStore()
        self.categories: EntityStore = EntityStore()
        self.crops: EntityStore = EntityStore()
        self.harvests: EntityStore = EntityStore()
        self.listings: EntityStore = EntityStore()
        self.offers: EntityStore = EntityStore()
        self.orders: EntityStore = EntityStore()
        self.contracts: EntityStore = EntityStore()
        self.deliveries: EntityStore = EntityStore()
        self.export_shipments: EntityStore = EntityStore()
        self.certificates: EntityStore = EntityStore()
        self.storage_lots: EntityStore = EntityStore()
        self.notifications: EntityStore = EntityStore()
        self.documents: EntityStore = EntityStore()
        self.payments: EntityStore = EntityStore()
        self.crm_leads: EntityStore = EntityStore()

    def reset(self) -> None:
        for attr in vars(self).values():
            if isinstance(attr, EntityStore):
                attr.reset()


agro_store = AgroStore()
