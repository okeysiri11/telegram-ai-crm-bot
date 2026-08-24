# CRM automation — durable follow-ups, priority, due evaluation, manager queue.

from __future__ import annotations

import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from applications.auto_marketplace.activities.service import ActivityService, activity_service
from applications.auto_marketplace.calendar.service import CalendarService, calendar_service
from applications.auto_marketplace.crm.models import (
    CRMLeadStatus,
    CRMTask,
    DealStage,
    Reminder,
    TaskPriority,
    TaskStatus,
)
from applications.auto_marketplace.deals.service import DealService, deal_service
from applications.auto_marketplace.leads.service import LeadService, lead_service
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.tasks.service import TaskService, task_service

DUE_WINDOW_SECONDS = 3600.0
DEFAULT_DELAY_HOURS = 24.0
_OPEN_FOLLOW_UPS = frozenset({"pending", "triggered"})
_CLOSED_DEAL_STAGES = frozenset({DealStage.CLOSED_WON, DealStage.CLOSED_LOST})
_CLOSED_LEAD_STATUSES = frozenset({CRMLeadStatus.LOST})
_PRIORITY_RANK = {
    TaskPriority.LOW: 0,
    TaskPriority.NORMAL: 1,
    TaskPriority.HIGH: 2,
    TaskPriority.URGENT: 3,
}


class FollowUpActionType(str, Enum):
    CALL = "call"
    EMAIL = "email"
    MEETING = "meeting"
    REMINDER = "reminder"
    TASK = "task"
    MANUAL_FOLLOW_UP = "manual_follow_up"


class FollowUpActionStatus(str, Enum):
    UPCOMING = "upcoming"
    DUE = "due"
    OVERDUE = "overdue"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


def parse_utc_timestamp(value: object, *, field: str = "due_at") -> float:
    """Parse unix seconds or ISO-8601. Naive datetimes are treated as UTC."""
    if value is None or value == "":
        raise ValidationError(f"{field} is required")
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValidationError(f"{field} must be a unix timestamp or ISO-8601 datetime") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).timestamp()


def parse_action_type(raw: object) -> FollowUpActionType:
    if raw is None or raw == "":
        return FollowUpActionType.MANUAL_FOLLOW_UP
    try:
        return FollowUpActionType(str(raw))
    except ValueError as exc:
        allowed = ", ".join(item.value for item in FollowUpActionType)
        raise ValidationError(f"invalid action_type: {raw!r}; allowed: {allowed}") from exc


def parse_priority(raw: object) -> TaskPriority:
    if raw is None or raw == "":
        return TaskPriority.NORMAL
    try:
        return TaskPriority(str(raw))
    except ValueError as exc:
        raise ValidationError(f"invalid priority: {raw!r}") from exc


def classify_follow_up_status(reminder: Reminder, *, now: float) -> FollowUpActionStatus:
    if reminder.status == "completed":
        return FollowUpActionStatus.COMPLETED
    if reminder.status in {"dismissed", "cancelled"}:
        return FollowUpActionStatus.CANCELLED
    if reminder.trigger_at < now:
        return FollowUpActionStatus.OVERDUE
    if reminder.trigger_at <= now + DUE_WINDOW_SECONDS:
        return FollowUpActionStatus.DUE
    return FollowUpActionStatus.UPCOMING


def calculate_priority(
    *,
    now: float,
    due_at: float,
    deal_stage: DealStage | None = None,
    lead_status: CRMLeadStatus | None = None,
    explicit: TaskPriority | None = None,
) -> TaskPriority:
    """Deterministic CRM action priority. No AI scoring."""
    chosen = TaskPriority.NORMAL
    overdue = now - due_at if due_at < now else 0.0
    if overdue >= 7 * 86400:
        chosen = TaskPriority.URGENT
    elif overdue >= 86400:
        chosen = TaskPriority.HIGH
    elif overdue >= 3600:
        chosen = TaskPriority.HIGH
    elif overdue > 0:
        chosen = TaskPriority.NORMAL
    elif due_at <= now + DUE_WINDOW_SECONDS:
        chosen = TaskPriority.NORMAL
    else:
        chosen = TaskPriority.LOW
    if deal_stage == DealStage.APPROVAL:
        chosen = _max_priority(chosen, TaskPriority.URGENT)
    elif deal_stage in {DealStage.NEGOTIATION, DealStage.PROPOSAL}:
        chosen = _max_priority(chosen, TaskPriority.HIGH)
    if lead_status == CRMLeadStatus.NEW and due_at <= now + DUE_WINDOW_SECONDS:
        chosen = _max_priority(chosen, TaskPriority.HIGH)
    if explicit is not None:
        chosen = _max_priority(chosen, explicit)
    return chosen


def _max_priority(left: TaskPriority, right: TaskPriority) -> TaskPriority:
    return left if _PRIORITY_RANK[left] >= _PRIORITY_RANK[right] else right


class CRMAutomationEngine:
    """Deterministic follow-up scheduler + due evaluator on durable Task/Reminder rows."""

    def __init__(
        self,
        *,
        leads: LeadService | None = None,
        deals: DealService | None = None,
        tasks: TaskService | None = None,
        calendar: CalendarService | None = None,
        activities: ActivityService | None = None,
    ) -> None:
        self._leads = leads or lead_service
        self._deals = deals or deal_service
        self._tasks = tasks or task_service
        self._calendar = calendar or calendar_service
        self._activities = activities or activity_service

    async def schedule_follow_up(
        self,
        *,
        lead_id: str = "",
        deal_id: str = "",
        customer_id: str = "",
        action_type: FollowUpActionType | str = FollowUpActionType.MANUAL_FOLLOW_UP,
        due_at: object | None = None,
        delay_hours: float | None = None,
        assigned_to: str = "",
        message: str = "",
        source: str = "manual",
        priority: TaskPriority | str | None = None,
        idempotency_key: str = "",
        now: float | None = None,
    ) -> dict[str, Any]:
        clock = now if now is not None else time.time()
        action = parse_action_type(action_type)
        explicit = parse_priority(priority)
        if due_at not in (None, ""):
            trigger_at = parse_utc_timestamp(due_at, field="due_at")
        else:
            try:
                hours = DEFAULT_DELAY_HOURS if delay_hours is None else float(delay_hours)
            except (TypeError, ValueError) as exc:
                raise ValidationError("delay_hours must be a number") from exc
            trigger_at = clock + hours * 3600
        await self._assert_open_entities(lead_id=lead_id, deal_id=deal_id, customer_id=customer_id)
        key = idempotency_key or self._default_intake_key(lead_id, deal_id, customer_id, action)
        existing = await self._find_open_by_key(key)
        if existing is not None:
            return self._follow_up_dict(existing, now=clock)
        lead_status, deal_stage, assignee, customer_id = await self._context(
            lead_id=lead_id, deal_id=deal_id, customer_id=customer_id, assigned_to=assigned_to
        )
        computed = calculate_priority(
            now=clock,
            due_at=trigger_at,
            deal_stage=deal_stage,
            lead_status=lead_status,
            explicit=explicit,
        )
        title = message or f"Follow-up: {action.value}"
        reminder = Reminder(
            customer_id=customer_id,
            lead_id=lead_id,
            deal_id=deal_id,
            title=title,
            message=title,
            assigned_agent_id=assignee,
            trigger_at=trigger_at,
            action_type=action.value,
            source=source,
            priority=computed.value,
            idempotency_key=key,
        )
        saved = await self._calendar.create_reminder(reminder)
        await self._record(
            "follow_up_scheduled",
            subject="Follow-up scheduled",
            body=action.value,
            reminder=saved,
            key=f"follow_up_scheduled:{saved.reminder_id}",
        )
        await self._sync_lead_next_action(lead_id, now=clock)
        return self._follow_up_dict(saved, now=clock)

    async def reschedule_follow_up(self, follow_up_id: str, *, due_at: object, now: float | None = None) -> dict[str, Any]:
        clock = now if now is not None else time.time()
        reminder = await self._calendar.get_reminder(follow_up_id)
        self._assert_open(reminder)
        await self._assert_open_entities(lead_id=reminder.lead_id, deal_id=reminder.deal_id, customer_id=reminder.customer_id)
        trigger_at = parse_utc_timestamp(due_at, field="due_at")
        lead_status, deal_stage, _, _ = await self._context(
            lead_id=reminder.lead_id, deal_id=reminder.deal_id, customer_id=reminder.customer_id, assigned_to=reminder.assigned_agent_id
        )
        priority = calculate_priority(
            now=clock,
            due_at=trigger_at,
            deal_stage=deal_stage,
            lead_status=lead_status,
            explicit=parse_priority(reminder.priority),
        )
        updated = await self._calendar.update_reminder(
            follow_up_id,
            trigger_at=trigger_at,
            priority=priority.value,
        )
        if updated.task_id:
            await self._tasks.update(updated.task_id, due_at=trigger_at, priority=priority)
        await self._record(
            "follow_up_rescheduled",
            subject="Follow-up rescheduled",
            body=str(int(trigger_at)),
            reminder=updated,
            key=f"follow_up_rescheduled:{updated.reminder_id}:{int(trigger_at)}",
        )
        await self._sync_lead_next_action(updated.lead_id, now=clock)
        return self._follow_up_dict(updated, now=clock)

    async def complete_follow_up(self, follow_up_id: str, *, now: float | None = None) -> dict[str, Any]:
        clock = now if now is not None else time.time()
        reminder = await self._calendar.get_reminder(follow_up_id)
        if reminder.status == "completed":
            return self._follow_up_dict(reminder, now=clock)
        saved = await self._calendar.complete_reminder(follow_up_id)
        if saved.task_id:
            try:
                await self._tasks.complete(saved.task_id)
            except NotFoundError:
                pass
        await self._record(
            "follow_up_completed",
            subject="Follow-up completed",
            body=saved.action_type,
            reminder=saved,
            key=f"follow_up_completed:{saved.reminder_id}",
        )
        await self._sync_lead_next_action(saved.lead_id, now=clock)
        return self._follow_up_dict(saved, now=clock)

    async def cancel_follow_up(self, follow_up_id: str, *, now: float | None = None) -> dict[str, Any]:
        clock = now if now is not None else time.time()
        reminder = await self._calendar.get_reminder(follow_up_id)
        if reminder.status in {"dismissed", "cancelled"}:
            return self._follow_up_dict(reminder, now=clock)
        saved = await self._calendar.dismiss_reminder(follow_up_id)
        if saved.task_id:
            try:
                await self._tasks.update(saved.task_id, status=TaskStatus.CANCELLED)
            except NotFoundError:
                pass
        await self._record(
            "follow_up_cancelled",
            subject="Follow-up cancelled",
            body=saved.action_type,
            reminder=saved,
            key=f"follow_up_cancelled:{saved.reminder_id}",
        )
        await self._sync_lead_next_action(saved.lead_id, now=clock)
        return self._follow_up_dict(saved, now=clock)

    async def get_follow_up(self, follow_up_id: str, *, now: float | None = None) -> dict[str, Any]:
        clock = now if now is not None else time.time()
        reminder = await self._calendar.get_reminder(follow_up_id)
        return self._follow_up_dict(reminder, now=clock)

    async def get_due_follow_ups(self, *, now: float | None = None) -> list[dict[str, Any]]:
        clock = now if now is not None else time.time()
        items = [
            self._follow_up_dict(item, now=clock)
            for item in await self._open_reminders()
            if item.trigger_at <= clock + DUE_WINDOW_SECONDS
        ]
        return sorted(items, key=lambda row: row["due_at"])

    async def get_overdue_follow_ups(self, *, now: float | None = None) -> list[dict[str, Any]]:
        clock = now if now is not None else time.time()
        items = [
            self._follow_up_dict(item, now=clock)
            for item in await self._open_reminders()
            if item.trigger_at < clock
        ]
        return sorted(items, key=lambda row: row["due_at"])

    async def list_follow_ups(self, *, now: float | None = None, due: bool = False, overdue: bool = False) -> list[dict[str, Any]]:
        if overdue:
            return await self.get_overdue_follow_ups(now=now)
        if due:
            return await self.get_due_follow_ups(now=now)
        clock = now if now is not None else time.time()
        items = [self._follow_up_dict(item, now=clock) for item in await self._open_reminders()]
        return sorted(items, key=lambda row: row["due_at"])

    async def next_action(
        self,
        *,
        lead_id: str = "",
        deal_id: str = "",
        customer_id: str = "",
        now: float | None = None,
    ) -> dict[str, Any] | None:
        clock = now if now is not None else time.time()
        candidates = [
            item
            for item in await self._open_reminders()
            if (not lead_id or item.lead_id == lead_id)
            and (not deal_id or item.deal_id == deal_id)
            and (not customer_id or item.customer_id == customer_id)
        ]
        if not candidates:
            return None
        earliest = min(candidates, key=lambda item: (item.trigger_at, item.created_at))
        payload = self._follow_up_dict(earliest, now=clock)
        return {
            "next_action_type": payload["action_type"],
            "next_action_at": payload["due_at"],
            "next_action_status": payload["status"],
            "next_action_priority": payload["priority"],
            "next_action_source": payload["source"],
            "follow_up_id": payload["follow_up_id"],
            "task_id": payload["task_id"],
            "entity_type": "follow_up",
            "entity_id": payload["follow_up_id"],
        }

    async def evaluate_due_actions(self, *, now: float | None = None) -> dict[str, Any]:
        clock = now if now is not None else time.time()
        processed = 0
        created_tasks = 0
        cancelled = 0
        skipped_closed = 0
        for reminder in await self._open_reminders():
            processed += 1
            if await self._is_closed(lead_id=reminder.lead_id, deal_id=reminder.deal_id):
                await self.cancel_follow_up(reminder.reminder_id, now=clock)
                cancelled += 1
                skipped_closed += 1
                continue
            status = classify_follow_up_status(reminder, now=clock)
            if status not in {FollowUpActionStatus.DUE, FollowUpActionStatus.OVERDUE}:
                continue
            created = await self._ensure_automation_task(reminder, now=clock)
            if created:
                created_tasks += 1
        return {
            "evaluated": processed,
            "tasks_created": created_tasks,
            "cancelled_closed": cancelled,
            "skipped_closed": skipped_closed,
            "due": await self.get_due_follow_ups(now=clock),
            "overdue": await self.get_overdue_follow_ups(now=clock),
        }

    async def get_action_queue(self, *, now: float | None = None, limit: int = 100) -> dict[str, Any]:
        clock = now if now is not None else time.time()
        items = [self._queue_item(item, now=clock) for item in await self._open_reminders()]
        items.sort(key=self._queue_sort_key)
        return {"items": items[: max(1, limit)], "generated_at": clock}

    def _queue_item(self, reminder: Reminder, *, now: float) -> dict[str, Any]:
        payload = self._follow_up_dict(reminder, now=now)
        overdue_seconds = max(0.0, now - reminder.trigger_at) if reminder.trigger_at < now else 0.0
        return {
            "entity_type": "follow_up",
            "entity_id": reminder.reminder_id,
            "follow_up_id": reminder.reminder_id,
            "customer_id": reminder.customer_id,
            "lead_id": reminder.lead_id,
            "deal_id": reminder.deal_id,
            "task_id": reminder.task_id,
            "action_type": payload["action_type"],
            "due_at": reminder.trigger_at,
            "status": payload["status"],
            "priority": payload["priority"],
            "overdue_seconds": overdue_seconds,
            "assigned_to": reminder.assigned_agent_id,
            "source": reminder.source,
        }

    @staticmethod
    def _queue_sort_key(item: dict[str, Any]) -> tuple:
        status = item["status"]
        priority = item["priority"]
        if status == FollowUpActionStatus.OVERDUE.value:
            bucket = {"urgent": 0, "high": 1}.get(priority, 2)
        elif status == FollowUpActionStatus.DUE.value:
            bucket = 3
        else:
            bucket = 4
        return (bucket, -float(item.get("overdue_seconds") or 0), float(item["due_at"]))

    async def _ensure_automation_task(self, reminder: Reminder, *, now: float) -> bool:
        existing = await self._linked_or_matching_task(reminder)
        lead_status, deal_stage, _, _ = await self._context(
            lead_id=reminder.lead_id, deal_id=reminder.deal_id, customer_id=reminder.customer_id, assigned_to=reminder.assigned_agent_id
        )
        priority = calculate_priority(
            now=now,
            due_at=reminder.trigger_at,
            deal_stage=deal_stage,
            lead_status=lead_status,
            explicit=parse_priority(reminder.priority),
        )
        if existing is not None:
            if existing.priority != priority or existing.due_at != reminder.trigger_at:
                await self._tasks.update(existing.task_id, priority=priority, due_at=reminder.trigger_at)
            if reminder.task_id != existing.task_id or reminder.priority != priority.value:
                await self._calendar.update_reminder(reminder.reminder_id, task_id=existing.task_id, priority=priority.value)
            return False
        task = CRMTask(
            title=reminder.title or f"Follow-up: {reminder.action_type}",
            description=reminder.message,
            customer_id=reminder.customer_id,
            lead_id=reminder.lead_id,
            deal_id=reminder.deal_id,
            assigned_agent_id=reminder.assigned_agent_id,
            created_by="crm-automation",
            priority=priority,
            due_at=reminder.trigger_at,
            metadata={"automation_reminder_id": reminder.reminder_id, "source": "automation"},
        )
        created = await self._tasks.create(task)
        await self._calendar.update_reminder(reminder.reminder_id, task_id=created.task_id, priority=priority.value)
        await self._record(
            "automation_task_created",
            subject="Automatic CRM task generated",
            body=created.task_id,
            reminder=reminder,
            key=f"automation_task:{reminder.reminder_id}",
            task_id=created.task_id,
        )
        return True

    async def _linked_or_matching_task(self, reminder: Reminder) -> CRMTask | None:
        if reminder.task_id:
            try:
                return await self._tasks.get(reminder.task_id)
            except NotFoundError:
                pass
        for task in await self._tasks.list_tasks(lead_id=reminder.lead_id or None, deal_id=reminder.deal_id or None):
            if (task.metadata or {}).get("automation_reminder_id") == reminder.reminder_id:
                return task
        return None

    async def _open_reminders(self) -> list[Reminder]:
        return [item for item in await self._calendar.list_reminders() if item.status in _OPEN_FOLLOW_UPS]

    async def _find_open_by_key(self, key: str) -> Reminder | None:
        if not key:
            return None
        for item in await self._open_reminders():
            if item.idempotency_key == key:
                return item
        return None

    async def _assert_open_entities(self, *, lead_id: str, deal_id: str, customer_id: str) -> None:
        if await self._is_closed(lead_id=lead_id, deal_id=deal_id):
            raise ValidationError("closed CRM entity cannot receive new follow-up tasks")
        if not lead_id and not deal_id and not customer_id:
            raise ValidationError("lead_id, deal_id, or customer_id is required")

    async def _is_closed(self, *, lead_id: str, deal_id: str) -> bool:
        if deal_id:
            try:
                deal = await self._deals.get(deal_id)
            except NotFoundError:
                deal = None
            if deal is not None and deal.stage in _CLOSED_DEAL_STAGES:
                return True
        if lead_id:
            try:
                lead = await self._leads.get(lead_id)
            except NotFoundError:
                return False
            if lead.status in _CLOSED_LEAD_STATUSES:
                return True
            converted_deal = str(lead.metadata.get("converted_deal_id") or "")
            if converted_deal:
                try:
                    deal = await self._deals.get(converted_deal)
                except NotFoundError:
                    deal = None
                if deal is not None and deal.stage in _CLOSED_DEAL_STAGES:
                    return True
        return False

    async def _context(
        self, *, lead_id: str, deal_id: str, customer_id: str, assigned_to: str
    ) -> tuple[CRMLeadStatus | None, DealStage | None, str, str]:
        lead_status: CRMLeadStatus | None = None
        deal_stage: DealStage | None = None
        assignee = assigned_to
        resolved_customer = customer_id
        if lead_id:
            lead = await self._leads.get(lead_id)
            lead_status = lead.status
            assignee = assignee or lead.assigned_agent_id
            resolved_customer = resolved_customer or lead.customer_id
            deal_id = deal_id or str(lead.metadata.get("converted_deal_id") or "")
        if deal_id:
            deal = await self._deals.get(deal_id)
            deal_stage = deal.stage
            assignee = assignee or deal.owner_agent_id
            resolved_customer = resolved_customer or deal.customer_id
        return lead_status, deal_stage, assignee, resolved_customer

    async def _sync_lead_next_action(self, lead_id: str, *, now: float) -> None:
        if not lead_id:
            return
        try:
            lead = await self._leads.get(lead_id)
        except NotFoundError:
            return
        nxt = await self.next_action(lead_id=lead_id, now=now)
        meta = dict(lead.metadata)
        if nxt:
            meta["next_action"] = nxt
        else:
            meta.pop("next_action", None)
        await self._leads.update(lead_id, metadata=meta)

    async def _record(
        self,
        activity_type: str,
        *,
        subject: str,
        body: str,
        reminder: Reminder,
        key: str,
        task_id: str = "",
    ) -> None:
        await self._activities.record_event(
            activity_type,
            subject=subject,
            body=body,
            customer_id=reminder.customer_id,
            lead_id=reminder.lead_id,
            deal_id=reminder.deal_id,
            task_id=task_id or reminder.task_id,
            agent_id=reminder.assigned_agent_id,
            idempotency_key=key,
        )

    def _follow_up_dict(self, reminder: Reminder, *, now: float) -> dict[str, Any]:
        status = classify_follow_up_status(reminder, now=now)
        data = reminder.to_dict()
        data["status"] = status.value if reminder.status in _OPEN_FOLLOW_UPS else (
            FollowUpActionStatus.COMPLETED.value if reminder.status == "completed" else FollowUpActionStatus.CANCELLED.value
        )
        data["action_type"] = reminder.action_type or FollowUpActionType.MANUAL_FOLLOW_UP.value
        data["priority"] = reminder.priority or TaskPriority.NORMAL.value
        data["source"] = reminder.source or "manual"
        data["due_at"] = reminder.trigger_at
        data["follow_up_id"] = reminder.reminder_id
        return data

    @staticmethod
    def _assert_open(reminder: Reminder) -> None:
        if reminder.status in {"completed", "dismissed", "cancelled"}:
            raise ValidationError(f"follow-up is {reminder.status}")

    @staticmethod
    def _default_intake_key(lead_id: str, deal_id: str, customer_id: str, action: FollowUpActionType) -> str:
        entity = lead_id or deal_id or customer_id
        return f"follow_up:{entity}:{action.value}"


crm_automation = CRMAutomationEngine()
