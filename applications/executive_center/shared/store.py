"""Shared store for Executive Command Center (Sprint 12.3)."""

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


class ExecutiveCenterStore:
    def __init__(self) -> None:
        self.dashboards: EntityStore = EntityStore()
        self.kpis: EntityStore = EntityStore()
        self.metrics: EntityStore = EntityStore()
        self.activity: EntityStore = EntityStore()
        self.twins: EntityStore = EntityStore()
        self.twin_snapshots: EntityStore = EntityStore()
        self.health_checks: EntityStore = EntityStore()
        self.infra_samples: EntityStore = EntityStore()
        self.ai_sessions: EntityStore = EntityStore()
        self.reports: EntityStore = EntityStore()
        self.analytics: EntityStore = EntityStore()
        self.graphs: EntityStore = EntityStore()
        self.companies: EntityStore = EntityStore()
        self.organizations: EntityStore = EntityStore()
        self.regions: EntityStore = EntityStore()
        self.permissions: EntityStore = EntityStore()
        self.audits: EntityStore = EntityStore()

    def reset(self) -> None:
        for attr in vars(self).values():
            if isinstance(attr, EntityStore):
                attr.reset()


executive_center_store = ExecutiveCenterStore()
