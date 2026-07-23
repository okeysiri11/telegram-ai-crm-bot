"""Event dispatcher — publish, deliver, ack, retry, DLQ."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.event_platform.dead_letter_queue import DeadLetterQueue
from applications.enterprise_hub.event_platform.event_router import EventRouter
from applications.enterprise_hub.event_platform.event_store import EventStore
from applications.enterprise_hub.event_platform.retry_manager import RetryManager
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class EventDispatcher:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.events = EventStore(self.store)
        self.router = EventRouter(self.store)
        self.retries = RetryManager(self.store)
        self.dlq = DeadLetterQueue(self.store)

    def publish(
        self,
        *,
        event_type: str,
        source: str,
        payload: dict[str, Any] | None = None,
        author: str = "system",
        severity: str = "normal",
        version: str = "1.0",
        idempotency_key: str | None = None,
        fail_subscribers: list[str] | None = None,
        max_retries: int = 2,
    ) -> dict[str, Any]:
        signature = hashlib.sha256(
            f"{event_type}:{source}:{idempotency_key or ''}".encode()
        ).hexdigest()[:24]
        event = self.events.append(
            event_type=event_type,
            source=source,
            payload=payload,
            author=author,
            severity=severity,
            version=version,
            idempotency_key=idempotency_key,
            signature=signature,
        )
        route = self.router.route(event=event)
        deliveries = []
        fail_set = set(fail_subscribers or [])
        for target in route.get("targets") or []:
            attempts = 0
            delivered = False
            last_error = None
            while attempts <= max_retries:
                attempts += 1
                if target in fail_set:
                    last_error = f"handler error in {target}"
                    self.retries.schedule(event_id=event["event_id"], attempt=attempts, reason=last_error)
                    continue
                delivered = True
                break
            if delivered:
                deliveries.append(
                    {
                        "delivery_id": _id("evp_dlv"),
                        "subscriber": target,
                        "status": "acked",
                        "attempts": attempts,
                    }
                )
            else:
                dlq = self.dlq.enqueue(
                    event_id=event["event_id"],
                    error=last_error or "unknown",
                    attempts=attempts,
                )
                deliveries.append(
                    {
                        "delivery_id": _id("evp_dlv"),
                        "subscriber": target,
                        "status": "dead",
                        "attempts": attempts,
                        "dlq_id": dlq["dlq_id"],
                    }
                )
        if deliveries and all(d.get("status") == "acked" for d in deliveries):
            self.events.set_status(event_id=event["event_id"], status="processed")
        elif any(d.get("status") == "acked" for d in deliveries):
            self.events.set_status(event_id=event["event_id"], status="delivered")
        did = _id("evp_disp")
        return self.store.evp_dispatches.save(
            did,
            {
                "dispatch_id": did,
                "event_id": event["event_id"],
                "route_id": route["route_id"],
                "deliveries": deliveries,
                "signature": signature,
                "at": _now(),
            },
        )
