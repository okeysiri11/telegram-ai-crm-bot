"""Event router — resolve destination subscribers for an event."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.event_platform.subscription_manager import SubscriptionManager
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class EventRouter:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.subscriptions = SubscriptionManager(self.store)

    def route(self, *, event: dict[str, Any]) -> dict[str, Any]:
        targets = self.subscriptions.for_event(
            event_type=event.get("event_type", ""),
            severity=event.get("severity"),
        )
        rid = _id("evp_rt")
        return self.store.evp_routes.save(
            rid,
            {
                "route_id": rid,
                "event_id": event.get("event_id"),
                "targets": [t.get("subscriber") for t in targets],
                "subscription_ids": [t.get("subscription_id") for t in targets],
                "at": _now(),
            },
        )
