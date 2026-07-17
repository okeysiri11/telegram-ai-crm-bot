# NotificationService — manager/client notifications (PostgreSQL-backed).

from __future__ import annotations

import logging
from typing import Any

from database.session import get_session
from repositories.notification_repository import NotificationRepository
from services.pg_manager_delivery_engine import ManagerDeliveryEngineV1

logger = logging.getLogger(__name__)


class NotificationService:
    @staticmethod
    async def notify_managers_new_request(
        *,
        vertical: str,
        request_number: str,
        client_name: str = "",
        product: str = "",
        manager_telegram_id: int | None = None,
    ) -> None:
        if manager_telegram_id is None:
            from services.manager_service import manager_service

            mgr = await manager_service.resolve_manager_for_vertical(vertical)
            manager_telegram_id = mgr.get("telegram_id") if mgr else None

        if manager_telegram_id is None:
            logger.warning("No manager to notify for %s request %s", vertical, request_number)
            return

        text = (
            f"🆕 Новая заявка [{vertical.upper()}] #{request_number}\n"
            f"Клиент: {client_name or '—'}\n"
            f"Товар/описание: {product or '—'}"
        )
        await ManagerDeliveryEngineV1.send_to_manager(
            manager_telegram_id=int(manager_telegram_id),
            text=text,
            request_number=request_number,
        )

    @staticmethod
    async def notify_client(
        *,
        bot,
        telegram_id: int,
        text: str,
    ) -> bool:
        if bot is None:
            return False
        try:
            await bot.send_message(telegram_id, text)
            return True
        except Exception:
            logger.exception("Failed to notify client telegram_id=%s", telegram_id)
            return False

    @staticmethod
    async def notify_status_change(
        *,
        request_number: str,
        old_status: str,
        new_status: str,
        client_telegram_id: int | None = None,
        bot=None,
    ) -> None:
        if client_telegram_id and bot:
            await NotificationService.notify_client(
                bot=bot,
                telegram_id=client_telegram_id,
                text=(
                    f"Статус заявки #{request_number} изменён:\n"
                    f"{old_status} → {new_status}"
                ),
            )

    @staticmethod
    async def notify_assignment(
        *,
        request_number: str,
        manager_name: str,
        client_telegram_id: int | None = None,
        bot=None,
    ) -> None:
        if client_telegram_id and bot:
            await NotificationService.notify_client(
                bot=bot,
                telegram_id=client_telegram_id,
                text=(
                    f"Заявка #{request_number} назначена менеджеру {manager_name}."
                ),
            )

    @staticmethod
    async def notify_new_comment(
        *,
        request_number: str,
        author: str,
        comment: str,
        recipient_telegram_id: int,
        bot=None,
    ) -> None:
        if bot:
            await NotificationService.notify_client(
                bot=bot,
                telegram_id=recipient_telegram_id,
                text=f"💬 Комментарий к #{request_number} ({author}):\n{comment}",
            )

    @staticmethod
    async def persist_internal_notification(
        *,
        title: str,
        message: str,
        user_id: int | None = None,
        notification_type: str = "SYSTEM_ALERT",
        channel: str = "INTERNAL",
    ) -> dict[str, Any]:
        async with get_session() as session:
            row = await NotificationRepository(session).create(
                user_id=user_id,
                notification_type=notification_type,
                channel=channel,
                title=title,
                message=message,
            )
            return {"id": str(row.id), "status": row.status}


notification_service = NotificationService()
