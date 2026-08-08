"""Epic 45.2 — memory cleanup / retention."""

from __future__ import annotations

import time
from typing import Any

from platform_memory.continuity_store import continuity_store
from platform_memory.memory_permissions import MemoryPrincipal, can_delete


class MemoryCleanup:
    def purge_session(self, principal: MemoryPrincipal, *, older_than_hours: float = 24) -> dict[str, Any]:
        cutoff = time.time() - older_than_hours * 3600
        removed = 0
        for r in list(continuity_store.list_for(principal.owner_id, level="session", limit=1000)):
            if r.created_at < cutoff and can_delete(principal, r):
                continuity_store.remove(r.id)
                removed += 1
        return {"removed": removed, "level": "session", "older_than_hours": older_than_hours}

    def purge_unpinned_working(self, principal: MemoryPrincipal, *, older_than_days: float = 14) -> dict[str, Any]:
        cutoff = time.time() - older_than_days * 86400
        removed = 0
        for r in list(continuity_store.list_for(principal.owner_id, level="working", limit=1000)):
            if not r.pinned and r.updated_at < cutoff and can_delete(principal, r):
                continuity_store.remove(r.id)
                removed += 1
        return {"removed": removed, "level": "working", "older_than_days": older_than_days}

    def clear_owner(self, principal: MemoryPrincipal) -> int:
        n = 0
        for r in list(continuity_store.list_for(principal.owner_id, limit=5000)):
            if can_delete(principal, r):
                continuity_store.remove(r.id)
                n += 1
        return n


memory_cleanup = MemoryCleanup()
