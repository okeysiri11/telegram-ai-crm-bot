"""Communication Timeline — Sprint 22.6."""

from __future__ import annotations

from typing import Any


class CommunicationTimeline:
    def __init__(self) -> None:
        self._events: dict[str, list[dict[str, Any]]] = {}

    def record(
        self,
        *,
        customer_id: str,
        kind: str,
        channel: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not customer_id:
            raise ValueError("customer_id is required")
        event = {
            "customer_id": customer_id,
            "kind": kind,
            "channel": channel,
            "payload": dict(payload or {}),
        }
        self._events.setdefault(customer_id, []).append(event)
        return event

    def history(self, *, customer_id: str) -> dict[str, Any]:
        items = list(self._events.get(customer_id, []))
        return {
            "customer_id": customer_id,
            "events": items,
            "count": len(items),
            "kinds_supported": ["sent", "opened", "clicked", "replied", "delivery_error"],
        }
