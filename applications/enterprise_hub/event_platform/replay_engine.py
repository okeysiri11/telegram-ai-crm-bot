"""Replay engine — reprocess historical events."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.event_platform.event_store import EventStore
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class ReplayEngine:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.events = EventStore(self.store)

    def replay(
        self,
        *,
        event_ids: list[str] | None = None,
        from_sequence: int | None = None,
        to_sequence: int | None = None,
    ) -> dict[str, Any]:
        selected = []
        if event_ids:
            selected = [self.events.get(eid) for eid in event_ids]
        else:
            for e in self.events.list_all():
                seq = int(e.get("sequence", 0))
                if from_sequence is not None and seq < from_sequence:
                    continue
                if to_sequence is not None and seq > to_sequence:
                    continue
                selected.append(e)
        if not selected:
            raise ValidationError("no events to replay")
        replayed = []
        for e in selected:
            self.events.set_status(event_id=e["event_id"], status="replayed")
            replayed.append(e["event_id"])
        rid = _id("evp_rpl")
        return self.store.evp_replays.save(
            rid,
            {
                "replay_id": rid,
                "event_ids": replayed,
                "count": len(replayed),
                "at": _now(),
            },
        )
