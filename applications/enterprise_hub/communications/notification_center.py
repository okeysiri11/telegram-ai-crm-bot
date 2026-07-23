"""Notification Center — single publish entry for all platform modules."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.communications.models import CHANNELS, PRIORITIES
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class NotificationCenter:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def publish(
        self,
        *,
        source: str,
        event: str,
        recipient: str,
        subject: str = "",
        body: str = "",
        channel: str = "",
        priority: str = "",
        template: str = "",
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not source or not event or not recipient:
            raise ValidationError("source, event, and recipient required")
        ch = (channel or "").lower().strip()
        if ch and ch not in CHANNELS:
            raise ValidationError(f"channel must be one of {list(CHANNELS)}")
        pr = (priority or "").lower().strip()
        if pr and pr not in PRIORITIES:
            raise ValidationError(f"priority must be one of {list(PRIORITIES)}")
        nid = _id("comm_evt")
        return self.store.comm_events.save(
            nid,
            {
                "event_id": nid,
                "source": source.lower(),
                "event": event,
                "recipient": recipient,
                "subject": subject,
                "body": body,
                "channel": ch,
                "priority": pr,
                "template": template,
                "payload": payload or {},
                "status": "registered",
                "at": _now(),
            },
        )

    def list_events(self) -> list[dict[str, Any]]:
        return list(self.store.comm_events.list_all())

    def status(self) -> dict[str, Any]:
        return {"events": self.store.comm_events.count()}
