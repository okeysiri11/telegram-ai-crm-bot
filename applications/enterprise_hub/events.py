"""Event infrastructure — registry, bus, routing, logging, replay, DLQ."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class EventInfrastructure:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.event_kinds = list(DEFAULT_CONFIG.event_kinds)

    def register_event_type(self, *, name: str, kind: str = "domain", schema: str = "") -> dict[str, Any]:
        k = kind.lower().strip()
        if k not in self.event_kinds:
            raise ValidationError(f"kind must be one of {self.event_kinds}")
        if not name:
            raise ValidationError("name required")
        eid = _id("hub_etype")
        return self.store.event_types.save(
            eid,
            {
                "event_type_id": eid,
                "name": name,
                "kind": k,
                "schema": schema or name,
                "at": _now(),
            },
        )

    def publish(
        self,
        *,
        event_type: str,
        source: str,
        payload: dict[str, Any] | None = None,
        fail: bool = False,
    ) -> dict[str, Any]:
        if not event_type or not source:
            raise ValidationError("event_type and source required")
        eid = _id("hub_evt")
        status = "dead_letter" if fail else "published"
        event = self.store.events.save(
            eid,
            {
                "event_id": eid,
                "event_type": event_type,
                "source": source.lower(),
                "payload": payload or {},
                "status": status,
                "at": _now(),
            },
        )
        lid = _id("hub_elog")
        self.store.event_logs.save(
            lid,
            {
                "log_id": lid,
                "event_id": eid,
                "action": "publish",
                "detail": f"{source}:{event_type}",
                "at": _now(),
            },
        )
        rid = _id("hub_eroute")
        self.store.event_routes.save(
            rid,
            {
                "route_id": rid,
                "event_id": eid,
                "from_source": source.lower(),
                "to_target": "enterprise_hub",
                "status": "routed" if not fail else "failed",
                "at": _now(),
            },
        )
        if fail:
            did = _id("hub_dlq")
            self.store.dead_letters.save(
                did,
                {
                    "dead_letter_id": did,
                    "event_id": eid,
                    "reason": "processing_failed",
                    "at": _now(),
                },
            )
        return event

    def replay(self, *, event_id: str) -> dict[str, Any]:
        event = self.store.events.get(event_id)
        if event is None:
            raise NotFoundError(f"event not found: {event_id}")
        rid = _id("hub_replay")
        return self.store.event_replays.save(
            rid,
            {
                "replay_id": rid,
                "event_id": event_id,
                "event_type": event["event_type"],
                "status": "replayed",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "event_types": self.store.event_types.count(),
            "events": self.store.events.count(),
            "routes": self.store.event_routes.count(),
            "logs": self.store.event_logs.count(),
            "replays": self.store.event_replays.count(),
            "dead_letters": self.store.dead_letters.count(),
            "kinds": self.event_kinds,
        }
