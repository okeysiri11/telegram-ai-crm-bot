# Governance catalog — inventory of governed assets.

from __future__ import annotations

from typing import Any

from ecosystem.governance.models import CatalogEntry
from ecosystem.shared.exceptions import NotFoundError, ValidationError
from ecosystem.shared.store import EcosystemStore, ecosystem_store


class CatalogService:
    def __init__(self, store: EcosystemStore | None = None) -> None:
        self._store = store or ecosystem_store

    def register(
        self,
        name: str,
        *,
        entry_type: str = "application",
        version: str = "1.0.0",
        owner: str = "",
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> CatalogEntry:
        if not name:
            raise ValidationError("name is required")
        entry = CatalogEntry(
            name=name,
            entry_type=entry_type,
            version=version,
            owner=owner,
            tags=tags or [],
            metadata=metadata or {},
        )
        self._store.catalog_entries.save(entry.entry_id, entry)
        return entry

    def get(self, entry_id: str) -> CatalogEntry:
        entry = self._store.catalog_entries.get(entry_id)
        if entry is None:
            raise NotFoundError("CatalogEntry", entry_id)
        return entry

    def list_entries(self, *, entry_type: str = "") -> list[CatalogEntry]:
        entries = self._store.catalog_entries.list_all()
        if entry_type:
            entries = [e for e in entries if e.entry_type == entry_type]
        return entries

    def sync_from_lifecycle(self) -> list[CatalogEntry]:
        created = []
        for record in self._store.lifecycle_records.list_all():
            existing = next((e for e in self._store.catalog_entries.list_all() if e.name == record.name and e.entry_type == record.kind.value), None)
            if existing:
                continue
            created.append(
                self.register(
                    record.name,
                    entry_type=record.kind.value,
                    version=record.version,
                    owner="lifecycle",
                    tags=[record.state.value],
                    metadata={"entity_id": record.entity_id},
                )
            )
        return created


catalog_service = CatalogService()
