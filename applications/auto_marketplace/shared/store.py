# In-memory entity store for marketplace foundation.

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


class MarketplaceStore:
    """Central in-memory persistence for Sprint 6.1 foundation."""

    def __init__(self) -> None:
        self.vehicles: EntityStore = EntityStore()
        self.dealers: EntityStore = EntityStore()
        self.customers: EntityStore = EntityStore()
        self.leads: EntityStore = EntityStore()
        self.deals: EntityStore = EntityStore()
        self.reservations: EntityStore = EntityStore()
        self.inspections: EntityStore = EntityStore()
        self.trade_ins: EntityStore = EntityStore()
        self.auctions: EntityStore = EntityStore()
        self.payments: EntityStore = EntityStore()
        self.invoices: EntityStore = EntityStore()
        self.deliveries: EntityStore = EntityStore()
        self.service_history: EntityStore = EntityStore()
        self.warranties: EntityStore = EntityStore()
        self.documents: EntityStore = EntityStore()
        self.catalog_vehicles: EntityStore = EntityStore()
        self.media: EntityStore = EntityStore()
        self.warehouses: EntityStore = EntityStore()
        self.brands: EntityStore = EntityStore()

    def reset(self) -> None:
        for store in (
            self.vehicles,
            self.dealers,
            self.customers,
            self.leads,
            self.deals,
            self.reservations,
            self.inspections,
            self.trade_ins,
            self.auctions,
            self.payments,
            self.invoices,
            self.deliveries,
            self.service_history,
            self.warranties,
            self.documents,
            self.catalog_vehicles,
            self.media,
            self.warehouses,
            self.brands,
        ):
            store.reset()


marketplace_store = MarketplaceStore()
