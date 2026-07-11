# Unified CalendarService for hub modules, tasks and future notifications.

from config import OWNER_ID, MANAGER_ID


class CalendarService:
    @staticmethod
    def can_access(user_id: int, event_row) -> bool:
        if not event_row:
            return False
        if user_id in (OWNER_ID, MANAGER_ID):
            return True
        if user_id in (event_row[5], event_row[6]):
            return True
        from services.permissions import PermissionService
        return PermissionService.is_crm_operator(user_id)

    @staticmethod
    def create_event(
        creator_id: int,
        title: str,
        start_time: str,
        description: str = "",
        module: str = "system",
        event_type: str = "general",
        owner_id: int = None,
        end_time: str = None,
        remind_before: int = 0,
        status: str = "PLANNED",
    ) -> int:
        from database import create_event
        return create_event(
            creator_id=creator_id,
            title=title,
            start_time=start_time,
            description=description,
            module=module,
            event_type=event_type,
            owner_id=owner_id,
            end_time=end_time,
            remind_before=remind_before,
            status=status,
        )

    @staticmethod
    def get_event(event_id: int, user_id: int):
        from database import get_event
        return get_event(event_id, user_id)

    @staticmethod
    def get_events_by_user(user_id: int, scope: str = "my", status: str = None, limit: int = 20):
        from database import get_events_by_user
        return get_events_by_user(user_id, scope=scope, status=status, limit=limit)

    @staticmethod
    def get_events_by_module(module: str, user_id: int = None, limit: int = 20):
        from database import get_events_by_module
        return get_events_by_module(module, user_id=user_id, limit=limit)

    @staticmethod
    def get_today_events(user_id: int, scope: str = "my", limit: int = 20):
        from database import get_today_events
        return get_today_events(user_id, scope=scope, limit=limit)

    @staticmethod
    def get_week_events(user_id: int, scope: str = "my", limit: int = 50):
        from database import get_week_events
        return get_week_events(user_id, scope=scope, limit=limit)

    @staticmethod
    def get_month_events(user_id: int, scope: str = "my", limit: int = 100):
        from database import get_month_events
        return get_month_events(user_id, scope=scope, limit=limit)

    @staticmethod
    def get_reminder_events(user_id: int, limit: int = 20):
        from database import get_reminder_events
        return get_reminder_events(user_id, limit=limit)

    @staticmethod
    def update_event(event_id: int, user_id: int, **fields) -> bool:
        from database import update_event
        return update_event(event_id, user_id, **fields)

    @staticmethod
    def delete_event(event_id: int, user_id: int) -> bool:
        from database import delete_event
        return delete_event(event_id, user_id)

    @staticmethod
    def sync_task_deadline(
        task_id: int,
        user_id: int,
        title: str,
        deadline: str,
        module: str = "system",
        assignee_id: int = None,
        existing_event_id: int = None,
    ) -> int:
        owner_id = assignee_id or user_id
        event_title = f"📋 Задача #{task_id}: {title}"
        description = f"task:{task_id}"

        if existing_event_id:
            CalendarService.update_event(
                existing_event_id,
                user_id,
                title=event_title,
                start_time=deadline,
                description=description,
                owner_id=owner_id,
                event_type="task",
                status="ACTIVE",
            )
            return existing_event_id

        return CalendarService.create_event(
            creator_id=user_id,
            title=event_title,
            start_time=deadline,
            description=description,
            module=module,
            event_type="task",
            owner_id=owner_id,
            remind_before=60,
            status="ACTIVE",
        )

    @staticmethod
    def remove_task_event(event_id: int) -> bool:
        if not event_id:
            return False
        from database import cursor, conn
        cursor.execute("DELETE FROM calendar_events WHERE id = ?", (event_id,))
        conn.commit()
        return cursor.rowcount > 0

    # --- NotificationService API (future) ---

    @staticmethod
    def get_pending_reminders(limit: int = 50):
        from database import get_events_needing_reminder
        return get_events_needing_reminder(limit=limit)

    @staticmethod
    def build_notification_payload(event_row: tuple) -> dict:
        from database import build_calendar_notification_payload
        return build_calendar_notification_payload(event_row)

    @staticmethod
    def dispatch_reminder_notifications(limit: int = 50) -> list[int]:
        """Create notifications for due reminders. Returns notification ids."""
        from database import register_module_notification
        created = []
        for event in CalendarService.get_pending_reminders(limit=limit):
            payload = CalendarService.build_notification_payload(event)
            nid = register_module_notification(
                payload["user_id"],
                payload["source_module"],
                title=payload["title"],
                message=payload["message"],
                priority=payload["priority"],
                is_reminder=True,
            )
            if nid:
                created.append(nid)
        return created
