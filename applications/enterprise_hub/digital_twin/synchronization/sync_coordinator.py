from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"



from applications.enterprise_hub.digital_twin.synchronization.conflict_resolution import ConflictResolution
from applications.enterprise_hub.digital_twin.synchronization.consistency import ConsistencyChecker
from applications.enterprise_hub.digital_twin.synchronization.event_listener import EventListener
from applications.enterprise_hub.digital_twin.synchronization.realtime_updates import RealtimeUpdates
from applications.enterprise_hub.digital_twin.timeline import TimelineEngine


class SyncCoordinator:
    """Sprint map `synchronization.py` — lives here to avoid package/module name clash."""

    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.listener = EventListener(self.store)
        self.realtime = RealtimeUpdates(self.store)
        self.conflicts = ConflictResolution(self.store)
        self.consistency = ConsistencyChecker(self.store)
        self.timeline = TimelineEngine(self.store)

    def ingest(
        self,
        *,
        source: str,
        event_type: str,
        twin_id: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        evt = self.listener.listen(source=source, event_type=event_type, twin_id=twin_id, payload=payload)
        upd = self.realtime.apply(twin_id=twin_id, payload=payload or {"last_event": event_type}, source=source)
        self.timeline.append(twin_id=twin_id, event=event_type, actor=source, detail=payload or {})
        return {"event_id": evt["event_id"], "update_id": upd["update_id"], "twin_id": twin_id}

    def status(self) -> dict[str, Any]:
        return {
            "listener": self.listener.status(),
            "realtime": self.realtime.status(),
            "conflicts": self.conflicts.status(),
            "consistency": self.consistency.status(),
        }
