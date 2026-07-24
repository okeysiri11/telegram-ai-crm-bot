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

from applications.enterprise_hub.api_standardization.models import EVENT_REQUIRED_FIELDS


class EventApiStandard:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def contract(self) -> dict[str, Any]:
        cid = _id("eas_evt")
        record = {
            "contract_id": cid,
            "required_fields": list(EVENT_REQUIRED_FIELDS),
            "envelope_example": {
                "id": "evt_example",
                "type": "domain.updated",
                "source": "enterprise_hub",
                "aggregate": "organization",
                "version": 1,
                "payload": {},
                "timestamp": _now(),
                "correlation_id": "corr_example",
            },
            "built_at": _now(),
        }
        self.store.eas_event_contracts.save(cid, record)
        return record

    def validate_event(self, event: dict[str, Any]) -> dict[str, Any]:
        missing = [f for f in EVENT_REQUIRED_FIELDS if f not in event]
        if missing:
            raise ValidationError(f"event missing fields: {', '.join(missing)}")
        eid = _id("eas_ev")
        record = {
            "validation_id": eid,
            "valid": True,
            "event_id": event.get("id"),
            "validated_at": _now(),
        }
        self.store.eas_event_validations.save(eid, record)
        return record

    def publish(self, event: dict[str, Any]) -> dict[str, Any]:
        self.validate_event(event)
        pid = event.get("id") or _id("evt")
        record = {**event, "id": pid, "published_at": _now()}
        self.store.eas_events.save(pid, record)
        return record
