# NotificationService — unified notifications with priority and channel support.

PRIORITY_MAP = {
    "LOW": "INFO",
    "NORMAL": "INFO",
    "HIGH": "WARNING",
    "CRITICAL": "CRITICAL",
    "INFO": "INFO",
    "WARNING": "WARNING",
}


class NotificationService:
    CHANNELS = ("TELEGRAM", "SYSTEM")

    @staticmethod
    def _normalize_priority(priority: str) -> str:
        return PRIORITY_MAP.get((priority or "NORMAL").upper(), "INFO")

    @staticmethod
    def create_notification(
        user_id: int,
        module: str,
        title: str,
        message: str = "",
        priority: str = "NORMAL",
        event_type: str = "general",
        channel: str = "SYSTEM",
        is_important: bool = False,
        is_reminder: bool = False,
    ) -> int:
        from database import create_notification, NOTIFICATION_CATEGORIES

        category = module if module in NOTIFICATION_CATEGORIES else "ai_assistant"
        db_priority = NotificationService._normalize_priority(priority)
        notification_id = create_notification(
            user_id=user_id,
            category=category,
            title=title,
            message=message,
            priority=db_priority,
            is_important=is_important,
            is_reminder=is_reminder,
            source_module=module,
        )
        if notification_id and channel == "TELEGRAM":
            NotificationService._mark_channel(notification_id, "TELEGRAM")
        return notification_id

    @staticmethod
    def _mark_channel(notification_id: int, channel: str) -> None:
        from database import cursor, conn
        cursor.execute(
            "UPDATE notifications SET channel = ? WHERE id = ?",
            (channel, notification_id),
        )
        conn.commit()

    @staticmethod
    async def send_notification(
        bot,
        user_id: int,
        module: str,
        title: str,
        message: str = "",
        priority: str = "NORMAL",
        event_type: str = "general",
    ) -> int:
        notification_id = NotificationService.create_notification(
            user_id=user_id,
            module=module,
            title=title,
            message=message,
            priority=priority,
            event_type=event_type,
            channel="TELEGRAM",
        )
        if bot and notification_id:
            icon = {"LOW": "ℹ️", "NORMAL": "📢", "HIGH": "⚠️", "CRITICAL": "🚨"}.get(
                priority.upper(), "📢",
            )
            text = f"{icon} {title}"
            if message:
                text += f"\n{message}"
            try:
                await bot.send_message(user_id, text)
                from database import cursor, conn
                from datetime import datetime
                cursor.execute(
                    "UPDATE notifications SET sent_at = ?, channel = 'TELEGRAM' WHERE id = ?",
                    (datetime.utcnow().isoformat(), notification_id),
                )
                conn.commit()
            except Exception:
                pass
        return notification_id

    @staticmethod
    def mark_read(notification_id: int, user_id: int) -> bool:
        from database import mark_notification_read, cursor, conn
        ok = mark_notification_read(notification_id, user_id)
        if ok:
            cursor.execute(
                "UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?",
                (notification_id, user_id),
            )
            conn.commit()
        return ok

    @staticmethod
    def archive_notification(notification_id: int, user_id: int) -> bool:
        from database import archive_notification
        return archive_notification(notification_id, user_id)

    @staticmethod
    def get_notifications(
        user_id: int,
        status: str = None,
        module: str = None,
        limit: int = 20,
    ):
        from database import get_notifications
        return get_notifications(user_id, status=status, category=module, limit=limit)

    @staticmethod
    def mark_all_read(user_id: int) -> int:
        from database import mark_all_notifications_read
        return mark_all_notifications_read(user_id)

    @staticmethod
    def archive_all_read(user_id: int) -> int:
        from database import archive_read_notifications
        return archive_read_notifications(user_id)
