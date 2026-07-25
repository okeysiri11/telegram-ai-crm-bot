"""Shared store — Platform Builder."""

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


class PlatformBuilderStore:
    def __init__(self) -> None:
        self.bootstraps: EntityStore = EntityStore()
        self.previews: EntityStore = EntityStore()
        self.creations: EntityStore = EntityStore()
        self.academy_sessions: EntityStore = EntityStore()
        self.god_actions: EntityStore = EntityStore()
        self.versions: EntityStore = EntityStore()

    def reset(self) -> None:
        for attr in vars(self).values():
            if isinstance(attr, EntityStore):
                attr.reset()


platform_builder_store = PlatformBuilderStore()
