# Portal push/in-app notifications.

from __future__ import annotations

from events.publisher import publish

from applications.auto_marketplace.authentication.models import PortalNotification
from applications.auto_marketplace.customer_portal.events import NotificationSentEvent
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class PortalNotificationService:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    async def send(self, user_id: str, *, title: str, body: str, channel: str = "push", metadata: dict | None = None) -> PortalNotification:
        notif = PortalNotification(user_id=user_id, title=title, body=body, channel=channel, metadata=metadata or {})
        self._store.portal_notifications.save(notif.notification_id, notif)
        await publish(NotificationSentEvent(notification_id=notif.notification_id, user_id=user_id, channel=channel))
        return notif

    def list_notifications(self, user_id: str, *, unread_only: bool = False) -> list[PortalNotification]:
        items = [n for n in self._store.portal_notifications.list_all() if n.user_id == user_id]
        if unread_only:
            items = [n for n in items if not n.read]
        return sorted(items, key=lambda n: n.created_at, reverse=True)

    def mark_read(self, notification_id: str) -> PortalNotification | None:
        notif = self._store.portal_notifications.get(notification_id)
        if notif:
            notif.read = True
            self._store.portal_notifications.save(notification_id, notif)
        return notif

    def register_push_device(self, user_id: str, device_token: str) -> dict:
        return {"user_id": user_id, "device_token": device_token, "registered": True}


portal_notification_service = PortalNotificationService()
