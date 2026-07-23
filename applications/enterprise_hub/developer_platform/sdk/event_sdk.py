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


class EventSdk:
    SURFACE = "events"

    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def capabilities(self) -> list[str]:
        return ["publish", "subscribe", "replay"]

    def invoke(self, *, method: str, plugin_id: str = "system", payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if method not in self.capabilities():
            raise ValidationError(f"unknown method for {self.SURFACE}: {method}")
        cid = _id("sdp_sdk")
        record = {
            "call_id": cid,
            "surface": self.SURFACE,
            "method": method,
            "plugin_id": plugin_id,
            "payload": payload or {},
            "result": {"ok": True, "surface": self.SURFACE, "method": method},
            "at": _now(),
        }
        return self.store.sdp_sdk_calls.save(cid, record)
