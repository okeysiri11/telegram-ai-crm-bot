"""LatencyAnalytics."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class LatencyAnalytics:
    kind = "latency"

    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def report(self) -> dict[str, Any]:
        events = self.store.evp_events.list_all()
        dispatches = self.store.evp_dispatches.list_all()
        retries = self.store.evp_retries.list_all()
        dlq = self.store.evp_dlq.list_all()
        subs = self.store.evp_subscriptions.list_all()
        aid = _id("evp_an")
        payload: dict[str, Any] = {
            "analytics_id": aid,
            "kind": self.kind,
            "event_count": len(events),
            "dispatch_count": len(dispatches),
            "retry_count": len(retries),
            "dlq_count": len(dlq),
            "subscriber_count": len(subs),
            "at": _now(),
        }
        if self.kind == "throughput":
            payload["events_per_dispatch"] = (len(events) / len(dispatches)) if dispatches else 0.0
        elif self.kind == "latency":
            payload["avg_backoff_ms"] = (
                sum(float(r.get("backoff_ms", 0) or 0) for r in retries) / len(retries) if retries else 0.0
            )
        else:
            by_type: dict[str, int] = {}
            for e in events:
                by_type[e.get("event_type", "?")] = by_type.get(e.get("event_type", "?"), 0) + 1
            payload["by_type"] = by_type
            payload["queue_load"] = len([e for e in events if e.get("status") in ("published", "delivered")])
        return self.store.evp_analytics.save(aid, payload)
