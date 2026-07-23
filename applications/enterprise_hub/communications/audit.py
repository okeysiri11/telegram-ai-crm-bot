"""Communications audit journal."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class CommunicationsAudit:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def record(
        self,
        *,
        sender: str,
        recipient: str,
        route_id: str = "",
        template: str = "",
        status: str = "",
        delivery_confirmed: bool = False,
        read_confirmed: bool = False,
        retries: int = 0,
        detail: str = "",
    ) -> dict[str, Any]:
        if not sender or not recipient:
            raise ValidationError("sender and recipient required")
        aid = _id("comm_audit")
        return self.store.comm_audit.save(
            aid,
            {
                "audit_id": aid,
                "sender": sender,
                "recipient": recipient,
                "route_id": route_id,
                "template": template,
                "status": status,
                "delivery_confirmed": delivery_confirmed,
                "read_confirmed": read_confirmed,
                "retries": int(retries),
                "detail": detail,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"entries": self.store.comm_audit.count()}
