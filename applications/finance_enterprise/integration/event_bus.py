"""Enterprise financial event bus — registry, routing, validation, log, replay, monitor."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.finance_enterprise.config import DEFAULT_CONFIG
from applications.finance_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.finance_enterprise.shared.store import FinanceEnterpriseStore, finance_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class FinancialEventBus:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.platforms = list(DEFAULT_CONFIG.int_platforms)
        self.event_kinds = list(DEFAULT_CONFIG.int_event_kinds)

    def register_event_type(self, *, name: str, platform: str, schema: str = "") -> dict[str, Any]:
        if not name:
            raise ValidationError("name required")
        plat = platform.lower().strip()
        if plat not in self.platforms:
            raise ValidationError(f"platform must be one of {self.platforms}")
        eid = _id("int_etype")
        return self.store.int_event_types.save(
            eid,
            {
                "event_type_id": eid,
                "name": name,
                "platform": plat,
                "schema": schema or name,
                "at": _now(),
            },
        )

    def publish(
        self,
        *,
        platform: str,
        event_kind: str,
        payload: dict[str, Any] | None = None,
        amount: float = 0.0,
        reference: str = "",
    ) -> dict[str, Any]:
        plat = platform.lower().strip()
        kind = event_kind.lower().strip()
        if plat not in self.platforms:
            raise ValidationError(f"platform must be one of {self.platforms}")
        if kind not in self.event_kinds:
            raise ValidationError(f"event_kind must be one of {self.event_kinds}")
        eid = _id("int_evt")
        event = self.store.int_events.save(
            eid,
            {
                "event_id": eid,
                "platform": plat,
                "event_kind": kind,
                "payload": payload or {},
                "amount": float(amount),
                "reference": reference,
                "status": "validated",
                "at": _now(),
            },
        )
        lid = _id("int_log")
        self.store.int_event_logs.save(
            lid,
            {
                "log_id": lid,
                "event_id": eid,
                "action": "publish",
                "detail": f"{plat}:{kind}",
                "at": _now(),
            },
        )
        rid = _id("int_route")
        self.store.int_routes.save(
            rid,
            {
                "route_id": rid,
                "event_id": eid,
                "from_platform": plat,
                "to_platform": "finance_enterprise",
                "status": "routed",
                "at": _now(),
            },
        )
        return event

    def replay(self, *, event_id: str) -> dict[str, Any]:
        event = self.store.int_events.get(event_id)
        if event is None:
            raise NotFoundError(f"event not found: {event_id}")
        rid = _id("int_replay")
        return self.store.int_replays.save(
            rid,
            {
                "replay_id": rid,
                "event_id": event_id,
                "platform": event["platform"],
                "event_kind": event["event_kind"],
                "status": "replayed",
                "at": _now(),
            },
        )

    def monitor(self) -> dict[str, Any]:
        mid = _id("int_mon")
        snapshot = {
            "events": self.store.int_events.count(),
            "routes": self.store.int_routes.count(),
            "logs": self.store.int_event_logs.count(),
            "replays": self.store.int_replays.count(),
        }
        return self.store.int_monitors.save(
            mid,
            {"monitor_id": mid, "snapshot": snapshot, "at": _now()},
        )

    def status(self) -> dict[str, Any]:
        return {
            "event_types": self.store.int_event_types.count(),
            "events": self.store.int_events.count(),
            "routes": self.store.int_routes.count(),
            "logs": self.store.int_event_logs.count(),
            "replays": self.store.int_replays.count(),
            "monitors": self.store.int_monitors.count(),
            "platforms": self.platforms,
            "event_kinds": self.event_kinds,
        }
