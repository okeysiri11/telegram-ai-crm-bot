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




class EventNormalizer:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def normalize(self, *, event_id: str | None = None) -> list[dict[str, Any]]:
        raw = self.store.epm_raw_events.list_all()
        if event_id:
            raw = [e for e in raw if e.get("event_id") == event_id]
            if not raw:
                raise NotFoundError(f"event not found: {event_id}")
        out = []
        for e in sorted(raw, key=lambda x: x.get("ts") or ""):
            nid = _id("epm_nev")
            activity = str(e.get("activity", "")).strip().lower().replace(" ", "_")
            record = {
                "normalized_id": nid,
                "event_id": e.get("event_id"),
                "case_id": e.get("case_id"),
                "activity": activity,
                "source": e.get("source"),
                "actor": e.get("actor"),
                "ts": e.get("ts"),
                "normalized_at": _now(),
            }
            self.store.epm_normalized.save(nid, record)
            out.append(record)
        return out

    def status(self) -> dict[str, Any]:
        return {"normalized_events": len(self.store.epm_normalized.list_all())}
