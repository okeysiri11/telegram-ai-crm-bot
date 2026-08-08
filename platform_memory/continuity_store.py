"""Epic 45.2 — shared continuous memory store (cross-channel, ACL-scoped)."""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


def _now() -> float:
    return time.time()


def new_id(prefix: str = "m") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


@dataclass
class MemoryRecord:
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

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "company_id": self.company_id,
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

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "company_id": self.company_id,
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

    def save(self, record: MemoryRecord) -> MemoryRecord:
        with self._lock:
            record.updated_at = _now()
            self.records[record.id] = record
            return record

    def get(self, memory_id: str) -> MemoryRecord | None:
        with self._lock:
            return self.records.get(memory_id)

    def remove(self, memory_id: str) -> bool:
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
    ) -> list[MemoryRecord]:
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
            return items[:limit]

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
