"""Event registry — type catalog with schemas and severity."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.event_platform.models import EVENT_TYPES, SEVERITIES
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class EventRegistry:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def register_type(
        self,
        *,
        event_type: str,
        version: str = "1.0",
        severity: str = "normal",
        schema: dict[str, Any] | None = None,
        description: str = "",
    ) -> dict[str, Any]:
        et = event_type.strip()
        if et not in EVENT_TYPES and not et:
            raise ValidationError("event_type is required")
        # allow custom types beyond catalog, but validate severity
        sev = severity.lower().strip()
        if sev not in SEVERITIES:
            raise ValidationError(f"severity must be one of {list(SEVERITIES)}")
        rid = _id("evp_type")
        return self.store.evp_types.save(
            rid,
            {
                "type_id": rid,
                "event_type": et,
                "version": version,
                "severity": sev,
                "schema": schema or {"type": "object"},
                "description": description,
                "registered_at": _now(),
            },
        )

    def get_type(self, type_id: str) -> dict[str, Any]:
        item = self.store.evp_types.get(type_id)
        if not item:
            raise NotFoundError(f"event type not found: {type_id}")
        return item

    def find_by_name(self, event_type: str) -> dict[str, Any] | None:
        for t in self.store.evp_types.list_all():
            if t.get("event_type") == event_type:
                return t
        return None

    def status(self) -> dict[str, Any]:
        return {"types": self.store.evp_types.count(), "catalog": list(EVENT_TYPES)}
