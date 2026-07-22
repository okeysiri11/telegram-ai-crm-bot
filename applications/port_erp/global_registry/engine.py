# Global Registry Engine — companies, partners, routes, assets, containers.

from __future__ import annotations

from applications.port_erp.enterprise.models import RegistryEntry, RegistryKind
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.store import PortStore, port_store


class GlobalRegistryEngine:
    """Canonical registry for the global port network."""

    def __init__(self, store: PortStore | None = None) -> None:
        self._store = store or port_store

    def kinds(self) -> list[str]:
        return [k.value for k in RegistryKind]

    def register(self, entry: RegistryEntry) -> RegistryEntry:
        if not entry.name:
            raise ValidationError("registry entry name is required")
        return self._store.global_registry.save(entry.entry_id, entry)

    def get(self, entry_id: str) -> RegistryEntry:
        entry = self._store.global_registry.get(entry_id)
        if entry is None:
            raise NotFoundError("registry_entry", entry_id)
        return entry

    def list_entries(self, kind: str | None = None) -> list[RegistryEntry]:
        items = self._store.global_registry.list_all()
        if kind:
            items = [e for e in items if e.kind.value == kind]
        return items

    def summary(self) -> dict[str, int]:
        counts: dict[str, int] = {k.value: 0 for k in RegistryKind}
        for entry in self.list_entries():
            counts[entry.kind.value] = counts.get(entry.kind.value, 0) + 1
        return counts


global_registry_engine = GlobalRegistryEngine()
