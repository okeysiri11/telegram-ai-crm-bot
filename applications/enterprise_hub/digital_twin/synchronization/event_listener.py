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



from applications.enterprise_hub.digital_twin.models import SYNC_SOURCES


class EventListener:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def listen(self, *, source: str, event_type: str, twin_id: str | None = None, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if source not in SYNC_SOURCES:
            raise ValidationError(f"invalid sync source: {source}")
        lid = _id("edt_evt")
        return self.store.edt_events.save(
            lid,
            {
                "event_id": lid,
                "source": source,
                "event_type": event_type,
                "twin_id": twin_id,
                "payload": payload or {},
                "received_at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"events": len(self.store.edt_events.list_all())}
