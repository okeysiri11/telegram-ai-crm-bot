"""Push Notification Center — Sprint 22.8."""

from __future__ import annotations

from typing import Any

from platform_client_portal.models import PUSH_KINDS


class PushNotificationCenter:
    def __init__(self) -> None:
        self._inbox: list[dict[str, Any]] = []

    def push(self, *, kind: str, title: str, customer_id: str, body: str = "") -> dict[str, Any]:
        if kind not in PUSH_KINDS:
            raise ValueError(f"unknown push kind: {kind}")
        event = {
            "kind": kind,
            "title": title,
            "body": body,
            "customer_id": customer_id,
            "channel": "push",
            "comms_hub_ref": "communications_hub",
            "read": False,
        }
        self._inbox.append(event)
        return event

    def inbox(self, *, customer_id: str) -> dict[str, Any]:
        items = [e for e in self._inbox if e.get("customer_id") == customer_id]
        return {"customer_id": customer_id, "events": items, "count": len(items), "kinds": list(PUSH_KINDS)}
