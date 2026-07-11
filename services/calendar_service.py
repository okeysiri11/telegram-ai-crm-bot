# Calendar integration for tasks and hub modules.


class CalendarService:
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
        from database import (
            create_calendar_event,
            update_calendar_event,
            CALENDAR_SOURCE_MODULES,
        )

        responsible = assignee_id or user_id
        cal_module = module if module in CALENDAR_SOURCE_MODULES else "calendar"
        event_title = f"📋 Задача #{task_id}: {title}"
        description = f"task:{task_id}"

        if existing_event_id:
            update_calendar_event(
                existing_event_id,
                user_id,
                title=event_title,
                start_datetime=deadline,
                description=description,
            )
            return existing_event_id

        return create_calendar_event(
            responsible_user=responsible,
            title=event_title,
            start_datetime=deadline,
            description=description,
            module=cal_module,
            priority="high",
        )

    @staticmethod
    def remove_task_event(event_id: int) -> bool:
        if not event_id:
            return False
        from database import cursor, conn
        cursor.execute("DELETE FROM calendar_events WHERE id = ?", (event_id,))
        conn.commit()
        return cursor.rowcount > 0
