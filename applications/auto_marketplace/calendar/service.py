# CalendarService — meetings and reminders.

from __future__ import annotations

import time

from events.publisher import publish
from applications.auto_marketplace.crm.events import ReminderTriggeredEvent
from applications.auto_marketplace.crm.models import Meeting, Reminder
from applications.auto_marketplace.shared.exceptions import NotFoundError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class CalendarService:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def schedule_meeting(self, meeting: Meeting) -> Meeting:
        return self._store.meetings.save(meeting.meeting_id, meeting)

    def get_meeting(self, meeting_id: str) -> Meeting:
        meeting = self._store.meetings.get(meeting_id)
        if meeting is None:
            raise NotFoundError("Meeting", meeting_id)
        return meeting

    def list_meetings(self, *, agent_id: str | None = None) -> list[Meeting]:
        items = self._store.meetings.list_all()
        if agent_id:
            items = [m for m in items if m.agent_id == agent_id]
        return sorted(items, key=lambda m: m.scheduled_at)

    def create_reminder(self, reminder: Reminder) -> Reminder:
        return self._store.reminders.save(reminder.reminder_id, reminder)

    async def trigger_due_reminders(self) -> list[Reminder]:
        now = time.time()
        triggered = []
        for reminder in self._store.reminders.list_all():
            if not reminder.triggered and reminder.trigger_at <= now:
                reminder.triggered = True
                self._store.reminders.save(reminder.reminder_id, reminder)
                await publish(
                    ReminderTriggeredEvent(
                        reminder_id=reminder.reminder_id,
                        task_id=reminder.task_id,
                        customer_id=reminder.customer_id,
                    )
                )
                triggered.append(reminder)
        return triggered


calendar_service = CalendarService()
