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



from applications.enterprise_hub.process_mining.models import EVENT_SOURCES


class EventCollector:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def collect(
        self,
        *,
        source: str,
        activity: str,
        case_id: str,
        actor: str = "system",
        ts: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if source not in EVENT_SOURCES:
            raise ValidationError(f"invalid event source: {source}")
        if not activity or not case_id:
            raise ValidationError("activity and case_id are required")
        eid = _id("epm_evt")
        return self.store.epm_raw_events.save(
            eid,
            {
                "event_id": eid,
                "source": source,
                "activity": activity,
                "case_id": case_id,
                "actor": actor,
                "ts": ts or _now(),
                "payload": payload or {},
                "collected_at": _now(),
            },
        )

    def collect_batch(self, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [self.collect(**e) for e in events]

    def status(self) -> dict[str, Any]:
        items = self.store.epm_raw_events.list_all()
        by_source: dict[str, int] = {}
        for i in items:
            s = i.get("source", "?")
            by_source[s] = by_source.get(s, 0) + 1
        return {"raw_events": len(items), "by_source": by_source}
