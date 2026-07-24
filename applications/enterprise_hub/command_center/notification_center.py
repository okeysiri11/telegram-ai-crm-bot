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

class NotificationCenter:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def notify(self, *, title: str, body: str = "", channel: str = "executive") -> dict[str, Any]:
        if not title:
            raise ValidationError("title is required")
        nid = _id("ecc_ntf")
        return self.store.ecc_notifications.save(
            nid,
            {
                "notification_id": nid,
                "title": title,
                "body": body,
                "channel": channel,
                "read": False,
                "created_at": _now(),
            },
        )

    def list_all(self) -> list[dict[str, Any]]:
        return self.store.ecc_notifications.list_all()

    def status(self) -> dict[str, Any]:
        return {"notifications": len(self.list_all())}
