"""Unified AI memory slice — wraps platform_memory; never isolated per client."""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from typing import Any

from platform_state.models import EntityMeta, compute_revision, utcnow


@dataclass
class MemoryRecord:
    memory_id: str
    scope: str  # user | workspace | conversation
    scope_id: str
    content: str
    category: str = "general"
    source_client: str | None = None
    tags: list[str] = field(default_factory=list)
    entity: EntityMeta | None = None
    created_at: str = field(default_factory=lambda: utcnow().isoformat())

    def __post_init__(self) -> None:
        if self.entity is None:
            self.entity = EntityMeta(entity_type="memory", entity_id=self.memory_id)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        if self.entity:
            d["entity"] = self.entity.to_dict()
        return d


class MemoryAdapter:
    """
    One memory belonging to User / Workspace / Conversation.
    In-process store + optional bridge to platform_memory.MemoryService.
    """

    def __init__(self) -> None:
        self._records: dict[str, MemoryRecord] = {}
        self._by_scope: dict[str, list[str]] = {}

    def _scope_key(self, scope: str, scope_id: str) -> str:
        return f"{scope}:{scope_id}"

    def store(
        self,
        *,
        scope: str,
        scope_id: str,
        content: str,
        category: str = "general",
        source_client: str | None = None,
        tags: list[str] | None = None,
        actor_id: str | None = None,
        memory_id: str | None = None,
    ) -> MemoryRecord:
        mid = memory_id or str(uuid.uuid4())
        rec = MemoryRecord(
            memory_id=mid,
            scope=scope,
            scope_id=scope_id,
            content=content,
            category=category,
            source_client=source_client,
            tags=list(tags or []),
        )
        if rec.entity:
            rec.entity.bump(updated_by=actor_id, source_client=source_client)
        self._records[mid] = rec
        key = self._scope_key(scope, scope_id)
        self._by_scope.setdefault(key, []).append(mid)
        return rec

    def list_scope(self, scope: str, scope_id: str, *, limit: int = 100) -> list[MemoryRecord]:
        ids = self._by_scope.get(self._scope_key(scope, scope_id), [])
        return [self._records[i] for i in ids if i in self._records][-limit:]

    def for_user_workspace_conversation(
        self,
        *,
        user_id: str | None = None,
        workspace_id: str | None = None,
        conversation_id: str | None = None,
        limit: int = 50,
    ) -> list[MemoryRecord]:
        out: list[MemoryRecord] = []
        if user_id:
            out.extend(self.list_scope("user", user_id, limit=limit))
        if workspace_id:
            out.extend(self.list_scope("workspace", workspace_id, limit=limit))
        if conversation_id:
            out.extend(self.list_scope("conversation", conversation_id, limit=limit))
        return out[:limit]

    def revision_token(self) -> str:
        parts = [(r.memory_id, r.entity.version if r.entity else 0) for r in self._records.values()]
        return compute_revision(parts)

    def snapshot(self, **scopes: str | None) -> dict[str, Any]:
        items = self.for_user_workspace_conversation(
            user_id=scopes.get("user_id"),
            workspace_id=scopes.get("workspace_id"),
            conversation_id=scopes.get("conversation_id"),
        )
        if not any(scopes.values()):
            items = list(self._records.values())[:100]
        return {
            "count": len(items),
            "revision": self.revision_token(),
            "records": [r.to_dict() for r in items],
            "note": "AI agents must read memory only via PlatformState",
        }

    def reset(self) -> None:
        self._records.clear()
        self._by_scope.clear()


memory_adapter = MemoryAdapter()
