# Audit trail service.

from __future__ import annotations

from typing import Any

from ecosystem.governance.models import AuditEntry
from ecosystem.shared.store import EcosystemStore, ecosystem_store


class AuditService:
    def __init__(self, store: EcosystemStore | None = None) -> None:
        self._store = store or ecosystem_store

    def record(
        self,
        action: str,
        *,
        actor: str = "system",
        resource_type: str = "",
        resource_id: str = "",
        details: dict[str, Any] | None = None,
    ) -> AuditEntry:
        entry = AuditEntry(
            action=action,
            actor=actor,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
        )
        self._store.audit_entries.save(entry.entry_id, entry)
        return entry

    def trail(self, *, resource_type: str = "", limit: int = 100) -> list[AuditEntry]:
        entries = self._store.audit_entries.list_all()
        if resource_type:
            entries = [e for e in entries if e.resource_type == resource_type]
        return sorted(entries, key=lambda e: e.created_at, reverse=True)[:limit]


audit_service = AuditService()
