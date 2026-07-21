# NotificationService — in-app notifications.

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from applications.agro_marketplace.shared.store import AgroStore, agro_store


@dataclass
class Notification:
    notification_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    recipient_id: str = ""
    channel: str = "in_app"
    title: str = ""
    body: str = ""
    read: bool = False
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "notification_id": self.notification_id,
            "recipient_id": self.recipient_id,
            "channel": self.channel,
            "title": self.title,
            "body": self.body,
            "read": self.read,
            "created_at": self.created_at,
        }


class NotificationService:
    def __init__(self, store: AgroStore | None = None) -> None:
        self._store = store or agro_store

    def reset(self) -> None:
        self._store.notifications.reset()

    def notify(self, recipient_id: str, title: str, body: str, *, channel: str = "in_app") -> Notification:
        note = Notification(recipient_id=recipient_id, title=title, body=body, channel=channel)
        return self._store.notifications.save(note.notification_id, note)

    def list_for(self, recipient_id: str) -> list[Notification]:
        return [n for n in self._store.notifications.list_all() if n.recipient_id == recipient_id]


notification_service = NotificationService()
