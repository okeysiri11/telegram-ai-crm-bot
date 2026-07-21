# Notification Center — multi-channel notifications for portal/mobile.

from __future__ import annotations

from events.publisher import publish

from applications.agro_marketplace.notifications.service import Notification, NotificationService, notification_service
from applications.agro_marketplace.portal.ai_integration import PortalAIIntegration, portal_ai
from applications.agro_marketplace.portal.events import NotificationSentEvent
from applications.agro_marketplace.portal.models import NotificationChannel
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class NotificationCenter:
    """Extends in-app notifications with push/email/sms/workflow/AI alert abstractions."""

    def __init__(
        self,
        store: AgroStore | None = None,
        notifications: NotificationService | None = None,
        ai: PortalAIIntegration | None = None,
    ) -> None:
        self._store = store or agro_store
        self._notifications = notifications or notification_service
        self._ai = ai or portal_ai

    async def send(
        self,
        recipient_id: str,
        title: str,
        body: str,
        *,
        channel: str | NotificationChannel = NotificationChannel.IN_APP,
    ) -> Notification:
        channel_value = channel.value if isinstance(channel, NotificationChannel) else channel
        note = self._notifications.notify(recipient_id, title, body, channel=channel_value)
        await publish(
            NotificationSentEvent(
                notification_id=note.notification_id,
                recipient_id=recipient_id,
                channel=channel_value,
                title=title,
            )
        )
        return note

    async def push(self, recipient_id: str, title: str, body: str) -> Notification:
        return await self.send(recipient_id, title, body, channel=NotificationChannel.PUSH)

    async def email(self, recipient_id: str, title: str, body: str) -> Notification:
        return await self.send(recipient_id, title, body, channel=NotificationChannel.EMAIL)

    async def sms(self, recipient_id: str, title: str, body: str) -> Notification:
        return await self.send(recipient_id, title, body, channel=NotificationChannel.SMS)

    async def workflow(self, recipient_id: str, title: str, body: str) -> Notification:
        return await self.send(recipient_id, title, body, channel=NotificationChannel.WORKFLOW)

    async def ai_alert(self, recipient_id: str, signal: str) -> Notification:
        payload = await self._ai.smart_notification(recipient_id, signal)
        return await self.send(
            recipient_id,
            payload["title"],
            payload["body"],
            channel=NotificationChannel.AI_ALERT,
        )

    def inbox(self, recipient_id: str) -> list[Notification]:
        return self._notifications.list_for(recipient_id)

    def mark_read(self, notification_id: str) -> Notification | None:
        note = self._store.notifications.get(notification_id)
        if note is None:
            return None
        note.read = True
        return self._store.notifications.save(notification_id, note)

    def metrics(self) -> dict:
        notes = self._store.notifications.list_all()
        by_channel: dict[str, int] = {}
        for n in notes:
            by_channel[n.channel] = by_channel.get(n.channel, 0) + 1
        return {"total": len(notes), "by_channel": by_channel}


notification_center = NotificationCenter()
