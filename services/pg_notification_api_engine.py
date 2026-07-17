# Notification API engine — HTTP-facing notification operations.

from __future__ import annotations

from typing import Any

from database.session import get_session
from repositories.notification_repository import NotificationRepository


class NotificationApiEngineV1:
    @staticmethod
    async def list_pending(*, limit: int = 100) -> list[dict[str, Any]]:
        async with get_session() as session:
            rows = await NotificationRepository(session).list_pending(limit=limit)
            return [
                {
                    "id": str(n.id),
                    "title": n.title,
                    "message": n.message,
                    "notification_type": n.notification_type,
                    "status": n.status,
                    "created_at": n.created_at.isoformat(),
                }
                for n in rows
            ]

    @staticmethod
    async def create(body: dict[str, Any]) -> dict[str, Any]:
        async with get_session() as session:
            notification = await NotificationRepository(session).create(
                user_id=body.get("user_id"),
                notification_type=body.get("notification_type", "SYSTEM_ALERT"),
                channel=body.get("channel", "INTERNAL"),
                title=body["title"],
                message=body["message"],
            )
            return {"id": str(notification.id), "status": notification.status}
