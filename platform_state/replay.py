"""Event Replay Engine — rebuild state from Event Store (Sprint 34.2D)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from platform_state.event_store import PlatformEventStore, StoredEvent, event_store
from platform_state.version_engine import VersionEngine, version_engine


ApplyFn = Callable[[StoredEvent], None]


@dataclass
class ReplayResult:
    applied: int
    skipped: int
    from_seq: int
    to_seq: int
    entity_ids: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "applied": self.applied,
            "skipped": self.skipped,
            "from_seq": self.from_seq,
            "to_seq": self.to_seq,
            "entity_ids": self.entity_ids,
            "errors": self.errors,
        }


class ReplayEngine:
    def __init__(
        self,
        store: PlatformEventStore | None = None,
        versions: VersionEngine | None = None,
    ) -> None:
        self._store = store or event_store
        self._versions = versions or version_engine

    def _apply_event(self, event: StoredEvent) -> bool:
        if event.after:
            self._versions.apply_from_event(event.after)
            return True
        if event.payload.get("action") == "created" and event.after is None:
            # Minimal create from payload
            data = dict(event.payload)
            data.pop("action", None)
            self._versions.apply_from_event(
                {
                    "id": event.entity_id,
                    "entity_type": event.entity_type,
                    "version": event.version,
                    "created_at": event.occurred_at,
                    "updated_at": event.occurred_at,
                    "created_by": event.actor_id,
                    "updated_by": event.actor_id,
                    "workspace_id": event.workspace_id,
                    "tenant_id": event.tenant_id,
                    "source_client": event.source_client,
                    "change_id": event.change_id or event.event_id,
                    "deleted_at": None,
                    "metadata": {},
                    "data": data,
                }
            )
            return True
        return False

    def replay_all(self, *, after_seq: int = 0, limit: int = 100_000) -> ReplayResult:
        events = self._store.since_seq(after_seq, limit=limit)
        return self._run(events)

    def replay_entity(
        self,
        entity_type: str,
        entity_id: str,
        *,
        after_seq: int = 0,
        limit: int = 50_000,
    ) -> ReplayResult:
        events = self._store.stream(entity_type, entity_id, after_seq=after_seq, limit=limit)
        return self._run(events)

    def replay_workspace(
        self,
        workspace_id: str,
        *,
        after_seq: int = 0,
        limit: int = 50_000,
    ) -> ReplayResult:
        events = self._store.workspace_stream(workspace_id, after_seq=after_seq, limit=limit)
        return self._run(events)

    def replay_partial(
        self,
        *,
        event_types: set[str] | None = None,
        after_seq: int = 0,
        limit: int = 50_000,
    ) -> ReplayResult:
        events = self._store.since_seq(after_seq, limit=limit)
        if event_types:
            events = [e for e in events if e.event_type in event_types]
        return self._run(events)

    def time_travel(
        self,
        *,
        at_or_before: str,
        entity_type: str | None = None,
        entity_id: str | None = None,
        workspace_id: str | None = None,
    ) -> ReplayResult:
        """Rebuild heads as of a point in time (debug / audit)."""
        events = self._store.until(
            at_or_before=at_or_before,
            entity_type=entity_type,
            entity_id=entity_id,
            workspace_id=workspace_id,
        )
        if entity_type and entity_id:
            # Clear only that stream head by replaying from empty for that key
            with self._versions._lock:
                k = self._versions.key(entity_type, entity_id)
                self._versions._heads.pop(k, None)
                self._versions._history.pop(k, None)
        return self._run(events)

    def audit_replay(
        self,
        *,
        entity_type: str | None = None,
        entity_id: str | None = None,
        workspace_id: str | None = None,
        limit: int = 5_000,
    ) -> list[dict[str, Any]]:
        if entity_type and entity_id:
            events = self._store.stream(entity_type, entity_id, limit=limit)
        elif workspace_id:
            events = self._store.workspace_stream(workspace_id, limit=limit)
        else:
            events = self._store.since_seq(0, limit=limit)
        return [e.to_dict() for e in events]

    def _run(self, events: list[StoredEvent]) -> ReplayResult:
        result = ReplayResult(
            applied=0,
            skipped=0,
            from_seq=events[0].seq if events else 0,
            to_seq=events[-1].seq if events else 0,
        )
        seen: set[str] = set()
        for event in events:
            try:
                ok = self._apply_event(event)
                if ok:
                    result.applied += 1
                    seen.add(f"{event.entity_type}:{event.entity_id}")
                else:
                    result.skipped += 1
            except Exception as exc:  # noqa: BLE001
                result.errors.append(f"{event.event_id}: {exc}")
                result.skipped += 1
        result.entity_ids = sorted(seen)
        return result


replay_engine = ReplayEngine()
