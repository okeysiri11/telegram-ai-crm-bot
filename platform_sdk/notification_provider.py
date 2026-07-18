# NotificationProvider — centralized notifications (handlers never call Telegram directly).

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def _notifications_allowed() -> bool:
    from platform_configuration.config_provider import config_provider

    return config_provider.is_notification_enabled()


class NotificationProvider:
    """All outbound notifications go through service layer delivery engines."""

    @staticmethod
    async def notify_created(
        *,
        vertical: str,
        request_number: str,
        client_name: str = "",
        product: str = "",
        manager_telegram_id: int | None = None,
        **_: Any,
    ) -> None:
        if not _notifications_allowed():
            logger.debug("notifications_disabled skip=notify_created")
            return
        from services.notification_service import notification_service

        await notification_service.notify_managers_new_request(
            vertical=vertical,
            request_number=request_number,
            client_name=client_name,
            product=product,
            manager_telegram_id=manager_telegram_id,
        )

    @staticmethod
    async def notify_assigned(
        *,
        request_number: str,
        manager_name: str,
        client_telegram_id: int | None = None,
        bot=None,
        **_: Any,
    ) -> None:
        if not _notifications_allowed():
            logger.debug("notifications_disabled skip=notify_assigned")
            return
        from services.notification_service import notification_service

        await notification_service.notify_assignment(
            request_number=request_number,
            manager_name=manager_name,
            client_telegram_id=client_telegram_id,
            bot=bot,
        )

    @staticmethod
    async def notify_completed(
        *,
        request_number: str,
        client_telegram_id: int | None = None,
        bot=None,
        **_: Any,
    ) -> None:
        if not _notifications_allowed():
            logger.debug("notifications_disabled skip=notify_completed")
            return
        from services.notification_service import notification_service

        if client_telegram_id and bot:
            await notification_service.notify_client(
                bot=bot,
                telegram_id=client_telegram_id,
                text=f"✅ Заявка #{request_number} завершена.",
            )

    @staticmethod
    async def notify_overdue(
        *,
        request_number: str,
        vertical: str,
        manager_telegram_id: int | None = None,
        overdue_seconds: int = 0,
        **_: Any,
    ) -> None:
        if not _notifications_allowed():
            logger.debug("notifications_disabled skip=notify_overdue")
            return
        from services.notification_service import notification_service

        title = f"SLA просрочена [{vertical.upper()}] #{request_number}"
        message = f"Просрочка: {overdue_seconds // 60} мин."
        await notification_service.persist_internal_notification(
            title=title,
            message=message,
            user_id=manager_telegram_id,
            notification_type="SLA_OVERDUE",
        )
        if manager_telegram_id:
            from platform_legacy import legacy

            await legacy.notifications.send_to_manager(
                manager_telegram_id=int(manager_telegram_id),
                text=f"⚠️ {title}\n{message}",
                request_number=request_number,
            )

    @staticmethod
    async def notify_owner(
        *,
        request_number: str,
        vertical: str,
        reason: str = "owner_escalation",
        **_: Any,
    ) -> None:
        from platform_configuration.config_provider import config_provider

        if not _notifications_allowed():
            logger.debug("notifications_disabled skip=notify_owner")
            return
        if not config_provider.is_feature_enabled("notifications.owner_notifications", default=True):
            logger.debug("owner_notifications_disabled")
            return
        from config import PLATFORM_OWNER_TELEGRAM_ID, PLATFORM_OWNER_NAME
        from services.notification_service import notification_service

        if PLATFORM_OWNER_TELEGRAM_ID is None:
            logger.warning("Owner telegram id not configured — skip owner notify")
            return

        title = f"Owner escalation [{vertical.upper()}] #{request_number}"
        message = f"{PLATFORM_OWNER_NAME}: {reason}"
        await notification_service.persist_internal_notification(
            title=title,
            message=message,
            user_id=PLATFORM_OWNER_TELEGRAM_ID,
            notification_type="OWNER_ESCALATION",
        )
        from platform_legacy import legacy

        await legacy.notifications.send_to_manager(
            manager_telegram_id=int(PLATFORM_OWNER_TELEGRAM_ID),
            text=f"🚨 {title}\n{message}",
            request_number=request_number,
        )


notification_provider = NotificationProvider()
