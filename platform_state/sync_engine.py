"""Platform Sync Engine — publish / subscribe / delta cursors (Sprint 34.2C)."""

from __future__ import annotations

import asyncio
import logging
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from events.event_bus import PlatformEventBus
from platform_state.events import PlatformStateChangedEvent
from platform_state.models import compute_revision, utcnow

logger = logging.getLogger(__name__)

SyncHandler = Callable[[PlatformStateChangedEvent], Awaitable[None] | None]


@dataclass
class SyncCursor:
    client_id: str
    last_revision: str
    last_seen_at: str
    slices: set[str] = field(default_factory=set)


class SyncEngine:
    """
    Cross-client synchronization on top of PlatformEventBus.
    Clients register cursors; reconnects receive deltas only.
    """

    def __init__(self) -> None:
        self._handlers: list[tuple[str, SyncHandler]] = []
        self._cursors: dict[str, SyncCursor] = {}
        self._recent: deque[dict[str, Any]] = deque(maxlen=500)
        self._revision = compute_revision("init", utcnow().isoformat())
        self._lock = asyncio.Lock()

    @property
    def revision(self) -> str:
        return self._revision

    def subscribe_client(self, handler_id: str, handler: SyncHandler) -> None:
        self._handlers.append((handler_id, handler))

    def register_cursor(
        self,
        client_id: str,
        *,
        last_revision: str | None = None,
        slices: list[str] | None = None,
    ) -> SyncCursor:
        cursor = SyncCursor(
            client_id=client_id,
            last_revision=last_revision or self._revision,
            last_seen_at=utcnow().isoformat(),
            slices=set(slices or []),
        )
        self._cursors[client_id] = cursor
        return cursor

    def get_cursor(self, client_id: str) -> SyncCursor | None:
        return self._cursors.get(client_id)

    async def publish_change(self, event: PlatformStateChangedEvent) -> dict[str, Any]:
        """Publish to Event Store + PlatformEventBus + sync subscribers + hot delta."""
        from platform_state.event_store import event_store
        from platform_state.telemetry import enterprise_telemetry

        with enterprise_telemetry.time_block("sync_latency"):
            self._revision = compute_revision(self._revision, event.event_id, event.revision)
            event.revision = self._revision
            record = {
                "event_id": event.event_id,
                "revision": self._revision,
                "slice_id": event.slice_id,
                "entity_type": event.entity_type,
                "entity_id": event.entity_id,
                "action": event.action,
                "source_client": event.source_client,
                "actor_id": event.actor_id,
                "version": event.version,
                "payload": event.payload,
                "occurred_at": event.occurred_at.isoformat(),
            }
            self._recent.append(record)
            enterprise_telemetry.gauge("queue_size", float(len(self._recent)))
            enterprise_telemetry.record_event()

            stored = event_store.append(
                event_type=event.event_type,
                entity_type=event.entity_type,
                entity_id=str(event.entity_id),
                payload={
                    "action": event.action,
                    "slice_id": event.slice_id,
                    "revision": self._revision,
                    **(event.payload or {}),
                },
                after=event.payload if isinstance(event.payload, dict) else None,
                version=int(event.version or 1),
                actor_id=event.actor_id,
                source_client=event.source_client,
                event_id=event.event_id,
                occurred_at=event.occurred_at.isoformat(),
            )
            record["seq"] = stored.seq

            bus_result = await PlatformEventBus.publish(event, wait=False)

            for handler_id, handler in list(self._handlers):
                try:
                    result = handler(event)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as exc:  # noqa: BLE001
                    logger.warning("sync handler %s failed: %s", handler_id, exc)
                    enterprise_telemetry.incr("failed_syncs")

        return {"revision": self._revision, "bus": bus_result, "event": record, "seq": stored.seq}

    def delta_since(self, last_revision: str | None, *, slices: list[str] | None = None) -> list[dict[str, Any]]:
        """Offline reconnect: return events after cursor revision."""
        if not last_revision:
            return list(self._recent)
        out: list[dict[str, Any]] = []
        seen = False
        slice_filter = set(slices or [])
        for rec in self._recent:
            if not seen:
                if rec["revision"] == last_revision:
                    seen = True
                continue
            if slice_filter and rec["slice_id"] not in slice_filter:
                continue
            out.append(rec)
        if not seen:
            # Unknown cursor — return all recent (safe full catch-up window)
            return [
                r
                for r in self._recent
                if not slice_filter or r["slice_id"] in slice_filter
            ]
        return out

    def status(self) -> dict[str, Any]:
        return {
            "revision": self._revision,
            "cursors": len(self._cursors),
            "recent_events": len(self._recent),
            "handlers": [h for h, _ in self._handlers],
        }

    def reset(self) -> None:
        self._handlers.clear()
        self._cursors.clear()
        self._recent.clear()
        self._revision = compute_revision("reset", utcnow().isoformat())


sync_engine = SyncEngine()
