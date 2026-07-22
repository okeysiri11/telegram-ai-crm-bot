"""Shared store for Workflow Studio (Sprint 12.2)."""

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


class WorkflowStudioStore:
    def __init__(self) -> None:
        self.workflows: EntityStore = EntityStore()
        self.nodes: EntityStore = EntityStore()
        self.connections: EntityStore = EntityStore()
        self.canvas_states: EntityStore = EntityStore()
        self.history: EntityStore = EntityStore()
        self.executions: EntityStore = EntityStore()
        self.breakpoints: EntityStore = EntityStore()
        self.logs: EntityStore = EntityStore()
        self.templates: EntityStore = EntityStore()
        self.versions: EntityStore = EntityStore()
        self.shares: EntityStore = EntityStore()
        self.permissions: EntityStore = EntityStore()
        self.metrics: EntityStore = EntityStore()
        self.ai_sessions: EntityStore = EntityStore()
        self.comments: EntityStore = EntityStore()
        self.groups: EntityStore = EntityStore()
        self.clipboard: EntityStore = EntityStore()

    def reset(self) -> None:
        for attr in vars(self).values():
            if isinstance(attr, EntityStore):
                attr.reset()


workflow_studio_store = WorkflowStudioStore()
