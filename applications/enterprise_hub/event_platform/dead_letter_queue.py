"""Dead letter queue — failed events with AI remediation hints."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.event_platform.event_store import EventStore
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class DeadLetterQueue:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.events = EventStore(self.store)

    def enqueue(
        self,
        *,
        event_id: str,
        error: str,
        attempts: int,
        recommendation: str | None = None,
    ) -> dict[str, Any]:
        event = self.events.get(event_id)
        self.events.set_status(event_id=event_id, status="dead")
        did = _id("evp_dlq")
        return self.store.evp_dlq.save(
            did,
            {
                "dlq_id": did,
                "event_id": event_id,
                "event_type": event.get("event_type"),
                "error": error,
                "attempts": int(attempts),
                "last_attempt_at": _now(),
                "recommendation": recommendation
                or "Inspect subscriber handler, fix schema mismatch, then replay",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"dead_letters": self.store.evp_dlq.count()}
