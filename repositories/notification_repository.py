# Notification Engine repository — PostgreSQL async data access.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.notification import (
    Notification,
    NotificationChannel,
    NotificationStatus,
    NotificationType,
)


class NotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        notification_type: str,
        channel: str,
        title: str,
        message: str,
        user_id: int | None = None,
        deal_id: uuid.UUID | None = None,
        status: str = NotificationStatus.PENDING.value,
        **extra: Any,
    ) -> Notification:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")

        if notification_type not in {t.value for t in NotificationType}:
            raise ValueError(f"Invalid notification_type: {notification_type}")
        if channel not in {c.value for c in NotificationChannel}:
            raise ValueError(f"Invalid channel: {channel}")
        if status not in {s.value for s in NotificationStatus}:
            raise ValueError(f"Invalid status: {status}")

        notification = Notification(
            user_id=user_id,
            deal_id=deal_id,
            notification_type=notification_type,
            channel=channel,
            title=title,
            message=message,
            status=status,
        )
        self._session.add(notification)
        await self._session.flush()
        return notification

    async def list_pending(self, *, limit: int = 100) -> list[Notification]:
        result = await self._session.execute(
            select(Notification)
            .where(Notification.status == NotificationStatus.PENDING.value)
            .order_by(Notification.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def mark_sent(self, notification_id: uuid.UUID) -> Notification | None:
        result = await self._session.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        notification = result.scalar_one_or_none()
        if notification is None:
            return None

        notification.status = NotificationStatus.SENT.value
        notification.sent_at = datetime.now(timezone.utc)
        await self._session.flush()
        return notification

    async def mark_failed(self, notification_id: uuid.UUID) -> Notification | None:
        result = await self._session.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        notification = result.scalar_one_or_none()
        if notification is None:
            return None

        notification.status = NotificationStatus.FAILED.value
        notification.retries = int(notification.retries or 0) + 1
        await self._session.flush()
        return notification
