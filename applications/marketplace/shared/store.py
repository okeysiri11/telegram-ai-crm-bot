"""Shared store for AI Marketplace (Sprint 12.1)."""

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

    def reset(self) -> None:
        self._items.clear()


class MarketplaceStore:
    def __init__(self) -> None:
        self.packages: EntityStore = EntityStore()
        self.plugins: EntityStore = EntityStore()
        self.connectors: EntityStore = EntityStore()
        self.workflows: EntityStore = EntityStore()
        self.applications: EntityStore = EntityStore()
        self.agents: EntityStore = EntityStore()
        self.installations: EntityStore = EntityStore()
        self.versions: EntityStore = EntityStore()
        self.licenses: EntityStore = EntityStore()
        self.ratings: EntityStore = EntityStore()
        self.security_scans: EntityStore = EntityStore()
        self.publications: EntityStore = EntityStore()
        self.org_markets: EntityStore = EntityStore()
        self.private_packages: EntityStore = EntityStore()
        self.downloads: EntityStore = EntityStore()

    def reset(self) -> None:
        for attr in vars(self).values():
            if isinstance(attr, EntityStore):
                attr.reset()


marketplace_store = MarketplaceStore()
