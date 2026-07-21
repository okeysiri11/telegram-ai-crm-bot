# Global memory — cross-application persistent memory.

from __future__ import annotations

import logging
from typing import Any

from ecosystem.assistant.models import MemoryEntry
from ecosystem.shared.store import EcosystemStore, ecosystem_store

logger = logging.getLogger(__name__)


class GlobalMemory:
    def __init__(self, store: EcosystemStore | None = None) -> None:
        self._store = store or ecosystem_store

    async def remember(
        self,
        user_id: str,
        content: str,
        *,
        application_id: str = "",
        memory_type: str = "episodic",
        tags: list[str] | None = None,
        importance: float = 0.5,
    ) -> MemoryEntry:
        entry = MemoryEntry(
            user_id=user_id,
            content=content,
            application_id=application_id,
            memory_type=memory_type,
            tags=tags or [],
            importance=importance,
        )
        self._store.global_memories.save(entry.memory_id, entry)
        try:
            from ecosystem.integrations.platform_bridge import platform_bridge

            await platform_bridge.store_memory(user_id, content, application_id=application_id)
        except Exception:
            logger.debug("platform memory bridge unavailable")
        return entry

    def recall(
        self,
        user_id: str,
        *,
        application_id: str = "",
        query: str = "",
        limit: int = 20,
    ) -> list[MemoryEntry]:
        entries = [m for m in self._store.global_memories.list_all() if m.user_id == user_id]
        if application_id:
            entries = [m for m in entries if m.application_id in ("", application_id)]
        if query:
            q = query.lower()
            entries = [
                m
                for m in entries
                if q in m.content.lower() or any(q in t.lower() for t in m.tags)
            ]
        return sorted(entries, key=lambda m: (m.importance, m.created_at), reverse=True)[:limit]

    def sync_from_shared(self, user_id: str) -> list[MemoryEntry]:
        """Pull cross-app shared AI memory into global memory."""
        synced: list[MemoryEntry] = []
        for shared in self._store.ai_memory.list_all():
            if shared.user_id != user_id:
                continue
            entry = MemoryEntry(
                user_id=user_id,
                content=shared.content,
                application_id=getattr(shared, "application_id", ""),
                memory_type="shared",
                tags=list(getattr(shared, "tags", [])),
            )
            self._store.global_memories.save(entry.memory_id, entry)
            synced.append(entry)
        return synced


global_memory = GlobalMemory()
