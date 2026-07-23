"""Event store — durable event history with sequence and status."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.event_platform.models import EVENT_STATUSES, SEVERITIES
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class EventStore:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def append(
        self,
        *,
        event_type: str,
        source: str,
        payload: dict[str, Any] | None = None,
        author: str = "system",
        severity: str = "normal",
        version: str = "1.0",
        idempotency_key: str | None = None,
        signature: str | None = None,
    ) -> dict[str, Any]:
        if not event_type:
            raise ValidationError("event_type is required")
        sev = severity.lower().strip()
        if sev not in SEVERITIES:
            raise ValidationError(f"severity must be one of {list(SEVERITIES)}")
        if idempotency_key:
            for e in self.store.evp_events.list_all():
                if e.get("idempotency_key") == idempotency_key:
                    return e
        seq = self.store.evp_events.count() + 1
        eid = _id("evp_evt")
        return self.store.evp_events.save(
            eid,
            {
                "event_id": eid,
                "event_type": event_type,
                "version": version,
                "source": source,
                "author": author,
                "severity": sev,
                "payload": payload or {},
                "sequence": seq,
                "status": "published",
                "idempotency_key": idempotency_key,
                "signature": signature,
                "created_at": _now(),
            },
        )

    def get(self, event_id: str) -> dict[str, Any]:
        item = self.store.evp_events.get(event_id)
        if not item:
            raise NotFoundError(f"event not found: {event_id}")
        return item

    def set_status(self, *, event_id: str, status: str) -> dict[str, Any]:
        event = self.get(event_id)
        st = status.lower().strip()
        if st not in EVENT_STATUSES:
            raise ValidationError(f"status must be one of {list(EVENT_STATUSES)}")
        event["status"] = st
        event["updated_at"] = _now()
        return self.store.evp_events.save(event_id, event)

    def list_all(self) -> list[dict[str, Any]]:
        return sorted(self.store.evp_events.list_all(), key=lambda e: e.get("sequence", 0))

    def status(self) -> dict[str, Any]:
        return {"events": self.store.evp_events.count()}
