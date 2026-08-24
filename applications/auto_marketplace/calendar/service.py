# CalendarService — meetings and reminders (durable via CRM persistence).

from __future__ import annotations

import time

from events.publisher import publish
from applications.auto_marketplace.crm.events import ReminderTriggeredEvent
from applications.auto_marketplace.crm.models import Meeting, Reminder
from applications.auto_marketplace.crm.persistence import CRMPersistence, get_crm_persistence
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store

_MEETING_STATUSES = frozenset({"scheduled", "completed", "cancelled"})
_REMINDER_STATUSES = frozenset({"pending", "triggered", "completed", "dismissed"})
_OPEN_REMINDERS = frozenset({"pending"})


class CalendarService:
    def __init__(
        self,
        store: MarketplaceStore | None = None,
        persistence: CRMPersistence | None = None,
    ) -> None:
        self._store = store or marketplace_store
        self._persistence = persistence

    def _records(self) -> CRMPersistence:
        return self._persistence or get_crm_persistence()

    async def _assert_relations(self, customer_id: str, lead_id: str, deal_id: str, task_id: str = "") -> None:
        records = self._records()
        if customer_id and await records.get_customer(customer_id) is None:
            raise NotFoundError("CustomerProfile", customer_id)
        if lead_id and await records.get_lead(lead_id) is None:
            raise NotFoundError("CRMLead", lead_id)
        if deal_id and await records.get_deal(deal_id) is None:
            raise NotFoundError("CRMDeal", deal_id)
        if task_id and await records.get_task(task_id) is None:
            raise NotFoundError("CRMTask", task_id)

    async def _record_event(self, activity_type: str, *, subject: str, body: str, entity, key: str) -> None:
        from applications.auto_marketplace.activities.service import activity_service

        await activity_service.record_event(
            activity_type,
            subject=subject,
            body=body,
            customer_id=getattr(entity, "customer_id", ""),
            lead_id=getattr(entity, "lead_id", ""),
            deal_id=getattr(entity, "deal_id", ""),
            task_id=getattr(entity, "task_id", ""),
            agent_id=getattr(entity, "agent_id", "") or getattr(entity, "assigned_agent_id", ""),
            idempotency_key=key,
        )

    async def schedule_meeting(self, meeting: Meeting) -> Meeting:
        await self._assert_relations(meeting.customer_id, meeting.lead_id, meeting.deal_id)
        meeting.updated_at = time.time()
        if meeting.status not in _MEETING_STATUSES:
            meeting.status = "scheduled"
        saved = await self._records().save_meeting(meeting)
        await self._record_event(
            "meeting",
            subject=saved.title or "Meeting",
            body=saved.location or saved.description,
            entity=saved,
            key=f"meeting:{saved.meeting_id}",
        )
        return saved

    async def get_meeting(self, meeting_id: str) -> Meeting:
        meeting = await self._records().get_meeting(meeting_id)
        if meeting is None:
            raise NotFoundError("Meeting", meeting_id)
        return meeting

    async def list_meetings(
        self,
        *,
        agent_id: str | None = None,
        customer_id: str | None = None,
        lead_id: str | None = None,
        deal_id: str | None = None,
        status: str | None = None,
    ) -> list[Meeting]:
        items = await self._records().list_meetings()
        if agent_id:
            items = [m for m in items if m.agent_id == agent_id]
        if customer_id:
            items = [m for m in items if m.customer_id == customer_id]
        if lead_id:
            items = [m for m in items if m.lead_id == lead_id]
        if deal_id:
            items = [m for m in items if m.deal_id == deal_id]
        if status:
            items = [m for m in items if m.status == status]
        return sorted(items, key=lambda m: m.scheduled_at)

    async def update_meeting(self, meeting_id: str, **updates: object) -> Meeting:
        meeting = await self.get_meeting(meeting_id)
        for key, value in updates.items():
            if not hasattr(meeting, key) or value is None:
                continue
            if key == "status" and str(value) not in _MEETING_STATUSES:
                raise ValidationError(f"invalid meeting status: {value!r}")
            setattr(meeting, key, value)
        if meeting.status == "completed":
            meeting.completed = True
        if meeting.status == "cancelled":
            meeting.completed = False
        await self._assert_relations(meeting.customer_id, meeting.lead_id, meeting.deal_id)
        meeting.updated_at = time.time()
        saved = await self._records().save_meeting(meeting)
        await self._record_event(
            "meeting",
            subject=saved.title or "Meeting updated",
            body=saved.status,
            entity=saved,
            key=f"meeting_updated:{saved.meeting_id}:{saved.status}",
        )
        return saved

    async def cancel_meeting(self, meeting_id: str) -> Meeting:
        meeting = await self.get_meeting(meeting_id)
        meeting.status = "cancelled"
        meeting.completed = False
        meeting.updated_at = time.time()
        saved = await self._records().save_meeting(meeting)
        await self._record_event(
            "meeting_cancelled",
            subject=saved.title or "Meeting cancelled",
            body="cancelled",
            entity=saved,
            key=f"meeting_cancelled:{saved.meeting_id}",
        )
        return saved

    async def delete_meeting(self, meeting_id: str) -> bool:
        await self.get_meeting(meeting_id)
        return await self._records().delete_meeting(meeting_id)

    async def create_reminder(self, reminder: Reminder) -> Reminder:
        await self._assert_relations(reminder.customer_id, reminder.lead_id, reminder.deal_id, reminder.task_id)
        reminder.updated_at = time.time()
        if not reminder.title:
            reminder.title = reminder.message
        saved = await self._records().save_reminder(reminder)
        await self._record_event(
            "reminder_created",
            subject=saved.title or saved.message or "Reminder",
            body=saved.message,
            entity=saved,
            key=f"reminder_created:{saved.reminder_id}",
        )
        return saved

    async def get_reminder(self, reminder_id: str) -> Reminder:
        item = await self._records().get_reminder(reminder_id)
        if item is None:
            raise NotFoundError("Reminder", reminder_id)
        return item

    async def list_reminders(
        self,
        *,
        customer_id: str | None = None,
        lead_id: str | None = None,
        deal_id: str | None = None,
        assigned_to: str | None = None,
        status: str | None = None,
        overdue: bool = False,
        due: bool = False,
        upcoming: bool = False,
        now: float | None = None,
    ) -> list[Reminder]:
        items = await self._records().list_reminders()
        if customer_id:
            items = [r for r in items if r.customer_id == customer_id]
        if lead_id:
            items = [r for r in items if r.lead_id == lead_id]
        if deal_id:
            items = [r for r in items if r.deal_id == deal_id]
        if assigned_to:
            items = [r for r in items if r.assigned_agent_id == assigned_to]
        if status:
            items = [r for r in items if r.status == status]
        clock = now if now is not None else time.time()
        if overdue:
            items = [r for r in items if r.status in _OPEN_REMINDERS and r.trigger_at < clock]
        elif due:
            items = [r for r in items if r.status in _OPEN_REMINDERS and r.trigger_at <= clock]
        elif upcoming:
            items = [r for r in items if r.status in _OPEN_REMINDERS and r.trigger_at > clock]
        return sorted(items, key=lambda r: (r.trigger_at, r.created_at))

    async def update_reminder(self, reminder_id: str, **updates: object) -> Reminder:
        reminder = await self.get_reminder(reminder_id)
        for key, value in updates.items():
            if key == "assigned_to":
                reminder.assigned_agent_id = str(value or "")
                continue
            if key == "remind_at":
                reminder.trigger_at = float(value) if value not in (None, "") else reminder.trigger_at
                continue
            if not hasattr(reminder, key) or value is None:
                continue
            if key == "status" and str(value) not in _REMINDER_STATUSES:
                raise ValidationError(f"invalid reminder status: {value!r}")
            setattr(reminder, key, value)
        await self._assert_relations(reminder.customer_id, reminder.lead_id, reminder.deal_id, reminder.task_id)
        reminder.updated_at = time.time()
        return await self._records().save_reminder(reminder)

    async def complete_reminder(self, reminder_id: str) -> Reminder:
        reminder = await self.get_reminder(reminder_id)
        if reminder.status == "completed":
            return reminder
        reminder.status = "completed"
        reminder.triggered = True
        reminder.updated_at = time.time()
        saved = await self._records().save_reminder(reminder)
        await self._record_event(
            "reminder_completed",
            subject=saved.title or "Reminder completed",
            body=saved.message,
            entity=saved,
            key=f"reminder_completed:{saved.reminder_id}",
        )
        return saved

    async def dismiss_reminder(self, reminder_id: str) -> Reminder:
        reminder = await self.get_reminder(reminder_id)
        reminder.status = "dismissed"
        reminder.updated_at = time.time()
        return await self._records().save_reminder(reminder)

    async def delete_reminder(self, reminder_id: str) -> bool:
        await self.get_reminder(reminder_id)
        return await self._records().delete_reminder(reminder_id)

    async def trigger_due_reminders(self) -> list[Reminder]:
        now = time.time()
        triggered: list[Reminder] = []
        for reminder in await self.list_reminders(due=True, now=now):
            reminder.triggered = True
            reminder.status = "triggered"
            reminder.updated_at = now
            saved = await self._records().save_reminder(reminder)
            await publish(
                ReminderTriggeredEvent(
                    reminder_id=saved.reminder_id,
                    task_id=saved.task_id,
                    customer_id=saved.customer_id,
                )
            )
            triggered.append(saved)
        return triggered


calendar_service = CalendarService()
