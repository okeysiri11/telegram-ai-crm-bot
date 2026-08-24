"""Epic 45.2 — shared continuous memory store (cross-channel, ACL-scoped)."""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from platform_memory.scope import MemoryScope, resolve_memory_scope

if TYPE_CHECKING:
    from platform_memory.memory_permissions import MemoryPrincipal


def _now() -> float:
    return time.time()


def new_id(prefix: str = "m") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


@dataclass
class MemoryRecord:
    """Sprint 47.0 (Decision 5): tenant_id is the canonical org identifier going
    forward; company_id is kept for backward compatibility and tenant_id mirrors it
    via __post_init__ when not explicitly supplied. "level" (session/working/project/
    long_term/knowledge) is a durability axis, distinct from the memory *scope*
    (PLATFORM/ORGANIZATION/VERTICAL/USER/CUSTOMER) introduced in Sprint 47.1 — do not
    conflate the two."""

    id: str
    owner_id: str
    company_id: str
    level: str  # session | working | project | long_term | knowledge
    kind: str  # conversation | task | project | document | preference | card | generation | ...
    title: str
    content: str
    channel: str = "web"
    project_id: str | None = None
    role: str = "owner"
    pinned: bool = False
    favorite: bool = False
    draft: bool = False
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] = field(default_factory=list)
    created_at: float = field(default_factory=_now)
    updated_at: float = field(default_factory=_now)
    tenant_id: str | None = None
    vertical: str | None = None
    customer_id: str | None = None

    def __post_init__(self) -> None:
        if self.tenant_id is None:
            self.tenant_id = self.company_id

    @property
    def scope(self) -> MemoryScope:
        return resolve_memory_scope(
            tenant_id=self.tenant_id,
            vertical=self.vertical,
            customer_id=self.customer_id,
            user_id=self.owner_id,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "company_id": self.company_id,
            "tenant_id": self.tenant_id,
            "vertical": self.vertical,
            "customer_id": self.customer_id,
            "scope": self.scope.value,
            "level": self.level,
            "kind": self.kind,
            "title": self.title,
            "content": self.content,
            "channel": self.channel,
            "project_id": self.project_id,
            "role": self.role,
            "pinned": self.pinned,
            "favorite": self.favorite,
            "draft": self.draft,
            "tags": list(self.tags),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class TimelineEvent:
    id: str
    owner_id: str
    company_id: str
    action: str
    title: str
    channel: str
    project_id: str | None = None
    ref_id: str | None = None
    created_at: float = field(default_factory=_now)
    metadata: dict[str, Any] = field(default_factory=dict)
    tenant_id: str | None = None

    def __post_init__(self) -> None:
        if self.tenant_id is None:
            self.tenant_id = self.company_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "company_id": self.company_id,
            "tenant_id": self.tenant_id,
            "action": self.action,
            "title": self.title,
            "channel": self.channel,
            "project_id": self.project_id,
            "ref_id": self.ref_id,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }


class ContinuityStore:
    """In-process continuous memory — same SoR for Telegram/Web/Desktop/Voice."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.records: dict[str, MemoryRecord] = {}
        self.timeline: list[TimelineEvent] = []
        self.sessions: dict[str, list[str]] = {}  # session_key -> record ids (turns)
        self.summaries: dict[str, dict[str, Any]] = {}

    def clear(self) -> None:
        with self._lock:
            self.records.clear()
            self.timeline.clear()
            self.sessions.clear()
            self.summaries.clear()

    def save(
        self, record: MemoryRecord, *, principal: "MemoryPrincipal | None" = None
    ) -> MemoryRecord | None:
        """Sprint 47.1: pass `principal` to enforce MemoryPrincipal ACL (can_write)
        centrally, here, instead of requiring every caller across platform_memory to
        remember to check it themselves. Omitting `principal` (the default) preserves
        every pre-Sprint-47.1 caller's exact behavior. Returns None if the write is
        denied — callers passing `principal` must handle that; callers not passing it
        keep getting the record back unconditionally, as before."""
        if principal is not None:
            from platform_memory.memory_permissions import can_write

            existing = self.records.get(record.id)
            if not can_write(principal, existing):
                return None
        with self._lock:
            record.updated_at = _now()
            self.records[record.id] = record
            return record

    def get(
        self, memory_id: str, *, principal: "MemoryPrincipal | None" = None
    ) -> MemoryRecord | None:
        """Sprint 47.1: pass `principal` to enforce can_read centrally (see save())."""
        with self._lock:
            rec = self.records.get(memory_id)
        if rec is None or principal is None:
            return rec
        from platform_memory.memory_permissions import can_read

        return rec if can_read(principal, rec) else None

    def remove(
        self, memory_id: str, *, principal: "MemoryPrincipal | None" = None
    ) -> bool:
        """Sprint 47.1: pass `principal` to enforce can_delete centrally (see save())."""
        if principal is not None:
            with self._lock:
                rec = self.records.get(memory_id)
            if rec is None:
                return False
            from platform_memory.memory_permissions import can_delete

            if not can_delete(principal, rec):
                return False
        with self._lock:
            return self.records.pop(memory_id, None) is not None

    def list_for(
        self,
        owner_id: str,
        *,
        company_id: str | None = None,
        level: str | None = None,
        kind: str | None = None,
        project_id: str | None = None,
        pinned: bool | None = None,
        favorite: bool | None = None,
        limit: int = 100,
        principal: "MemoryPrincipal | None" = None,
    ) -> list[MemoryRecord]:
        """Sprint 47.1: pass `principal` to additionally apply filter_readable — the
        richer, role/project-aware ACL (admin/owner cross-project visibility etc.),
        on top of the existing owner_id/company_id pre-filter below. For every
        pre-Sprint-47.1 caller (which always queries its own owner_id/company_id),
        this is a no-op: can_read's first check already matches. It only changes
        behavior for calls that start passing a principal whose scope differs from
        the raw owner_id/company_id filter."""
        with self._lock:
            items = []
            for r in self.records.values():
                if r.owner_id != owner_id:
                    continue
                if company_id and r.company_id != company_id:
                    continue
                if level and r.level != level:
                    continue
                if kind and r.kind != kind:
                    continue
                if project_id and r.project_id != project_id:
                    continue
                if pinned is not None and r.pinned != pinned:
                    continue
                if favorite is not None and r.favorite != favorite:
                    continue
                items.append(r)
            items.sort(key=lambda x: x.updated_at, reverse=True)
            items = items[:limit]
        if principal is None:
            return items
        from platform_memory.memory_permissions import filter_readable

        return filter_readable(principal, items)

    def add_timeline(self, event: TimelineEvent) -> TimelineEvent:
        with self._lock:
            self.timeline.append(event)
            return event

    def list_timeline(
        self,
        owner_id: str,
        *,
        company_id: str | None = None,
        since: float | None = None,
        until: float | None = None,
        limit: int = 200,
    ) -> list[TimelineEvent]:
        with self._lock:
            items = [
                e
                for e in self.timeline
                if e.owner_id == owner_id
                and (not company_id or e.company_id == company_id)
                and (since is None or e.created_at >= since)
                and (until is None or e.created_at <= until)
            ]
            items.sort(key=lambda x: x.created_at, reverse=True)
            return items[:limit]


continuity_store = ContinuityStore()
