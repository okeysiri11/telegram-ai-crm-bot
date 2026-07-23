"""Shared store — Enterprise Hub (Sprint 19.0)."""

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


class EnterpriseHubStore:
    def __init__(self) -> None:
        # Registry
        self.platforms: EntityStore = EntityStore()
        self.services: EntityStore = EntityStore()
        self.modules: EntityStore = EntityStore()
        self.integrations: EntityStore = EntityStore()
        self.organizations: EntityStore = EntityStore()
        self.environments: EntityStore = EntityStore()
        # Integration layer
        self.discoveries: EntityStore = EntityStore()
        self.routes: EntityStore = EntityStore()
        self.gateway_requests: EntityStore = EntityStore()
        self.aggregations: EntityStore = EntityStore()
        self.bus_messages: EntityStore = EntityStore()
        # Identity
        self.identities: EntityStore = EntityStore()
        self.org_mappings: EntityStore = EntityStore()
        self.users: EntityStore = EntityStore()
        self.role_mappings: EntityStore = EntityStore()
        self.permission_syncs: EntityStore = EntityStore()
        # Configuration
        self.global_config: EntityStore = EntityStore()
        self.feature_flags: EntityStore = EntityStore()
        self.platform_settings: EntityStore = EntityStore()
        self.env_profiles: EntityStore = EntityStore()
        self.config_registry: EntityStore = EntityStore()
        # Events
        self.event_types: EntityStore = EntityStore()
        self.events: EntityStore = EntityStore()
        self.event_routes: EntityStore = EntityStore()
        self.event_logs: EntityStore = EntityStore()
        self.event_replays: EntityStore = EntityStore()
        self.dead_letters: EntityStore = EntityStore()
        # Knowledge & dashboards
        self.knowledge: EntityStore = EntityStore()
        self.dashboards: EntityStore = EntityStore()

    def reset(self) -> None:
        for attr in vars(self).values():
            if isinstance(attr, EntityStore):
                attr.reset()


enterprise_hub_store = EnterpriseHubStore()
