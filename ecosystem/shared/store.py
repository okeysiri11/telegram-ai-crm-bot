# In-memory entity store for ecosystem layer.

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


class EcosystemStore:
    """Central in-memory persistence for Sprint 7.1."""

    def __init__(self) -> None:
        self.users: EntityStore = EntityStore()
        self.sessions: EntityStore = EntityStore()
        self.session_history: EntityStore = EntityStore()
        self.devices: EntityStore = EntityStore()
        self.mfa_enrollments: EntityStore = EntityStore()
        self.profiles: EntityStore = EntityStore()
        self.organizations: EntityStore = EntityStore()
        self.workspaces: EntityStore = EntityStore()
        self.departments: EntityStore = EntityStore()
        self.teams: EntityStore = EntityStore()
        self.projects: EntityStore = EntityStore()
        self.memberships: EntityStore = EntityStore()
        self.invitations: EntityStore = EntityStore()
        self.tenants: EntityStore = EntityStore()
        self.roles: EntityStore = EntityStore()
        self.role_assignments: EntityStore = EntityStore()
        self.activities: EntityStore = EntityStore()
        self.notifications: EntityStore = EntityStore()
        self.favorites: EntityStore = EntityStore()
        self.shared_files: EntityStore = EntityStore()
        self.shared_calendar: EntityStore = EntityStore()
        self.shared_contacts: EntityStore = EntityStore()
        self.shared_tasks: EntityStore = EntityStore()
        self.ai_memory: EntityStore = EntityStore()
        self.assistant_sessions: EntityStore = EntityStore()
        # Sprint 7.2 — Cross-Application Communication
        self.bus_events: EntityStore = EntityStore()
        self.envelopes: EntityStore = EntityStore()
        self.subscriptions: EntityStore = EntityStore()
        self.registrations: EntityStore = EntityStore()
        self.sync_records: EntityStore = EntityStore()
        self.delivery_confirmations: EntityStore = EntityStore()
        self.shared_contexts: EntityStore = EntityStore()
        self.dead_letters: EntityStore = EntityStore()
        self.event_store_log: EntityStore = EntityStore()

    def reset(self) -> None:
        for attr in vars(self).values():
            if isinstance(attr, EntityStore):
                attr.reset()


ecosystem_store = EcosystemStore()
