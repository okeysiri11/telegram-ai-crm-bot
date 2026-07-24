"""Notification center — Sprint 22.3."""

from __future__ import annotations

from typing import Any

from platform_beauty_workspace.models import NOTIFICATION_KINDS


class NotificationCenter:
    def __init__(self) -> None:
        self._events: list[dict[str, Any]] = []

    def publish(self, *, kind: str, title: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if kind not in NOTIFICATION_KINDS:
            raise ValueError(f"unknown notification kind: {kind}")
        event = {
            "kind": kind,
            "title": title,
            "payload": dict(payload or {}),
            "realtime": True,
            "read": False,
        }
        self._events.append(event)
        return event

    def list_events(self, *, unread_only: bool = False) -> dict[str, Any]:
        items = [e for e in self._events if (not unread_only or not e.get("read"))]
        return {"events": items, "count": len(items), "kinds": list(NOTIFICATION_KINDS)}

    def seed_defaults(self) -> list[dict[str, Any]]:
        seeds = [
            ("new_appointment", "New appointment booked"),
            ("open_slot", "Open slot available this afternoon"),
            ("ai_recommendation", "AI suggests win-back campaign"),
        ]
        return [self.publish(kind=k, title=t) for k, t in seeds]
