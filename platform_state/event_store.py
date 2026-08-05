"""Durable append-only Platform Event Store — Sprint 34.2D / 35.0 / 35.1.

Persists every business action. Survives process restart.
Default backend: JSONL + in-memory indexes (CI-safe).
Optional: ADOS_EVENT_STORE_BACKEND=postgres dual-writes to platform_state_events
without changing public APIs.
Does NOT replace PlatformEventBus.
"""

from __future__ import annotations

import json
import os
import threading
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from platform_state.models import utcnow

_DEFAULT_PATH = Path(
    os.environ.get(
        "ADOS_PLATFORM_EVENT_STORE",
        str(Path.home() / ".ados" / "platform_event_store.jsonl"),
    )
)


@dataclass(frozen=True)
class StoredEvent:
    seq: int
    event_id: str
    event_type: str
    entity_type: str
    entity_id: str
    workspace_id: str | None
    tenant_id: str | None
    change_id: str | None
    version: int
    actor_id: str | None
    source_client: str | None
    payload: dict[str, Any]
    before: dict[str, Any] | None
    after: dict[str, Any] | None
    occurred_at: str
    stream_key: str
    agent_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> StoredEvent:
        return cls(
            seq=int(raw["seq"]),
            event_id=str(raw["event_id"]),
            event_type=str(raw["event_type"]),
            entity_type=str(raw["entity_type"]),
            entity_id=str(raw["entity_id"]),
            workspace_id=raw.get("workspace_id"),
            tenant_id=raw.get("tenant_id"),
            change_id=raw.get("change_id"),
            version=int(raw.get("version") or 1),
            actor_id=raw.get("actor_id"),
            source_client=raw.get("source_client"),
            payload=dict(raw.get("payload") or {}),
            before=raw.get("before"),
            after=raw.get("after"),
            occurred_at=str(raw["occurred_at"]),
            stream_key=str(raw["stream_key"]),
            agent_id=raw.get("agent_id"),
        )


class PlatformEventStore:
    """Append-only immutable event log with stream queries."""

    def __init__(self, path: Path | str | None = None, *, memory: bool = False) -> None:
        self._memory = memory
        self._path = Path(path) if path else _DEFAULT_PATH
        self._lock = threading.RLock()
        self._events: list[StoredEvent] = []
        self._by_id: dict[str, StoredEvent] = {}
        self._seq = 0
        if not memory and str(self._path) not in {":memory:", ""}:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            # Migrate legacy sqlite filename hint → jsonl
            if self._path.suffix == ".sqlite3":
                self._path = self._path.with_suffix(".jsonl")
            self._load()

    def _load(self) -> None:
        if self._memory or not self._path.exists():
            return
        with self._lock:
            with self._path.open("r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        raw = json.loads(line)
                        ev = StoredEvent.from_dict(raw)
                    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                        continue
                    self._events.append(ev)
                    self._by_id[ev.event_id] = ev
                    self._seq = max(self._seq, ev.seq)

    def _persist(self, event: StoredEvent) -> None:
        if self._memory:
            return
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event.to_dict(), default=str) + "\n")

    def append(
        self,
        *,
        event_type: str,
        entity_type: str,
        entity_id: str,
        payload: dict[str, Any] | None = None,
        before: dict[str, Any] | None = None,
        after: dict[str, Any] | None = None,
        version: int = 1,
        actor_id: str | None = None,
        source_client: str | None = None,
        workspace_id: str | None = None,
        tenant_id: str | None = None,
        change_id: str | None = None,
        agent_id: str | None = None,
        event_id: str | None = None,
        occurred_at: str | None = None,
    ) -> StoredEvent:
        eid = event_id or str(uuid.uuid4())
        occurred = occurred_at or utcnow().isoformat()
        stream_key = f"{entity_type}:{entity_id}"
        with self._lock:
            if eid in self._by_id:
                return self._by_id[eid]
            self._seq += 1
            event = StoredEvent(
                seq=self._seq,
                event_id=eid,
                event_type=event_type,
                entity_type=entity_type,
                entity_id=entity_id,
                workspace_id=workspace_id,
                tenant_id=tenant_id,
                change_id=change_id,
                version=version,
                actor_id=actor_id,
                source_client=source_client,
                payload=dict(payload or {}),
                before=before,
                after=after,
                occurred_at=occurred,
                stream_key=stream_key,
                agent_id=agent_id,
            )
            self._events.append(event)
            self._by_id[eid] = event
            self._persist(event)
            self._maybe_postgres(event)
        return event

    def _maybe_postgres(self, event: StoredEvent) -> None:
        try:
            from platform_state.event_store_postgres import pg_safe_append, postgres_enabled

            if not postgres_enabled() or self._memory:
                return
            pg_safe_append(event.to_dict())
        except Exception:  # noqa: BLE001
            pass

    def get(self, event_id: str) -> StoredEvent | None:
        with self._lock:
            return self._by_id.get(event_id)

    def stream(
        self,
        entity_type: str,
        entity_id: str,
        *,
        after_seq: int = 0,
        limit: int = 10_000,
    ) -> list[StoredEvent]:
        key = f"{entity_type}:{entity_id}"
        with self._lock:
            out = [e for e in self._events if e.stream_key == key and e.seq > after_seq]
        return out[:limit]

    def workspace_stream(
        self,
        workspace_id: str,
        *,
        after_seq: int = 0,
        limit: int = 10_000,
    ) -> list[StoredEvent]:
        with self._lock:
            out = [
                e
                for e in self._events
                if e.workspace_id == workspace_id and e.seq > after_seq
            ]
        return out[:limit]

    def since_seq(self, after_seq: int = 0, *, limit: int = 10_000) -> list[StoredEvent]:
        with self._lock:
            out = [e for e in self._events if e.seq > after_seq]
        return out[:limit]

    def until(
        self,
        *,
        at_or_before: str,
        entity_type: str | None = None,
        entity_id: str | None = None,
        workspace_id: str | None = None,
        limit: int = 50_000,
    ) -> list[StoredEvent]:
        with self._lock:
            out: list[StoredEvent] = []
            for e in self._events:
                if e.occurred_at > at_or_before:
                    continue
                if entity_type and entity_id and e.stream_key != f"{entity_type}:{entity_id}":
                    continue
                if workspace_id and e.workspace_id != workspace_id:
                    continue
                out.append(e)
                if len(out) >= limit:
                    break
        return out

    def count(self) -> int:
        with self._lock:
            return len(self._events)

    def max_seq(self) -> int:
        with self._lock:
            return self._seq

    def reset(self) -> None:
        with self._lock:
            self._events.clear()
            self._by_id.clear()
            self._seq = 0
            if not self._memory and self._path.exists():
                self._path.write_text("", encoding="utf-8")

    def close(self) -> None:
        return None


def _use_memory_store() -> bool:
    flag = os.environ.get("ADOS_EVENT_STORE_MEMORY", "").lower()
    if flag in {"1", "true", "yes"}:
        return True
    if os.environ.get("ADOS_EVENT_STORE_DURABLE", "").lower() in {"1", "true", "yes"}:
        return False
    import sys

    return "pytest" in sys.modules


event_store = PlatformEventStore(memory=_use_memory_store())
