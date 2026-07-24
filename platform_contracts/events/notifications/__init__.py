"""Notification events — Sprint 21.3."""

from __future__ import annotations

from dataclasses import dataclass

from platform_contracts.events.base import BaseEvent


@dataclass
class NotificationRequestedEvent(BaseEvent):
    event_type: str = "notifications.requested"
