"""Shared store for AI OS (Sprint 12.4)."""

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


class AIOSStore:
    def __init__(self) -> None:
        self.schedules: EntityStore = EntityStore()
        self.processes: EntityStore = EntityStore()
        self.queues: EntityStore = EntityStore()
        self.bus_messages: EntityStore = EntityStore()
        self.memory: EntityStore = EntityStore()
        self.runtime_jobs: EntityStore = EntityStore()
        self.checkpoints: EntityStore = EntityStore()
        self.contexts: EntityStore = EntityStore()
        self.messages: EntityStore = EntityStore()
        self.clusters: EntityStore = EntityStore()
        self.nodes: EntityStore = EntityStore()
        self.logs: EntityStore = EntityStore()
        self.metrics: EntityStore = EntityStore()
        self.traces: EntityStore = EntityStore()
        self.alerts: EntityStore = EntityStore()

    def reset(self) -> None:
        for attr in vars(self).values():
            if isinstance(attr, EntityStore):
                attr.reset()


ai_os_store = AIOSStore()
