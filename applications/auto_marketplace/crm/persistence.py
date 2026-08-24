"""CRM persistence backends — Postgres is the production source of truth.

Set AUTO_CRM_PERSISTENCE=memory only for isolated unit tests. Production and
restart-durability tests leave the variable unset (or set to postgres).
"""

from __future__ import annotations

import os
from typing import Protocol

from applications.auto_marketplace.crm.models import (
    CRMDeal,
    CRMLead,
    CRMLeadStatus,
    CRMTask,
    CustomerProfile,
    DealStage,
    EmailMessage,
    Interaction,
    InteractionType,
    LeadSource,
    Meeting,
    PhoneCall,
    Reminder,
    TaskPriority,
    TaskStatus,
)
from applications.auto_marketplace.crm.tenant import current_crm_tenant
from applications.auto_marketplace.shared.store import EntityStore

_MEMORY_MODES = frozenset({"memory", "mem", "in_memory", "in-memory"})


def crm_persistence_mode() -> str:
    raw = os.environ.get("AUTO_CRM_PERSISTENCE", "").strip().lower()
    if raw in _MEMORY_MODES:
        return "memory"
    return "postgres"


def _lead_from_payload(data: dict) -> CRMLead:
    source_raw = data.get("source", LeadSource.WEB.value)
    status_raw = data.get("status", CRMLeadStatus.NEW.value)
    try:
        source = LeadSource(str(source_raw))
    except ValueError:
        source = LeadSource.WEB
    try:
        status = CRMLeadStatus(str(status_raw))
    except ValueError:
        status = CRMLeadStatus.NEW
    return CRMLead(
        lead_id=str(data.get("lead_id") or ""),
        customer_id=str(data.get("customer_id") or ""),
        vehicle_id=str(data.get("vehicle_id") or ""),
        dealer_id=str(data.get("dealer_id") or ""),
        source=source,
        status=status,
        score=float(data.get("score") or 0.0),
        assigned_agent_id=str(data.get("assigned_agent_id") or ""),
        notes=str(data.get("notes") or ""),
        metadata=dict(data.get("metadata") or {}) if isinstance(data.get("metadata"), dict) else {},
        created_at=float(data.get("created_at") or 0.0),
        qualified_at=float(data["qualified_at"]) if data.get("qualified_at") is not None else None,
    )


def _deal_from_payload(data: dict) -> CRMDeal:
    stage_raw = data.get("stage", DealStage.PROSPECT.value)
    try:
        stage = DealStage(str(stage_raw))
    except ValueError:
        stage = DealStage.PROSPECT
    return CRMDeal(
        deal_id=str(data.get("deal_id") or ""),
        opportunity_id=str(data.get("opportunity_id") or ""),
        customer_id=str(data.get("customer_id") or ""),
        dealer_id=str(data.get("dealer_id") or ""),
        vehicle_id=str(data.get("vehicle_id") or ""),
        stage=stage,
        amount=float(data.get("amount") or 0.0),
        probability=float(data.get("probability") or 0.1),
        win=data.get("win"),
        owner_agent_id=str(data.get("owner_agent_id") or ""),
        created_at=float(data.get("created_at") or 0.0),
        closed_at=float(data["closed_at"]) if data.get("closed_at") is not None else None,
    )


def _task_from_payload(data: dict) -> CRMTask:
    try:
        status = TaskStatus(str(data.get("status") or TaskStatus.PENDING.value))
    except ValueError:
        status = TaskStatus.PENDING
    try:
        priority = TaskPriority(str(data.get("priority") or TaskPriority.NORMAL.value))
    except ValueError:
        priority = TaskPriority.NORMAL
    due = data.get("due_at")
    completed = data.get("completed_at")
    return CRMTask(
        task_id=str(data.get("task_id") or ""),
        title=str(data.get("title") or ""),
        description=str(data.get("description") or ""),
        customer_id=str(data.get("customer_id") or ""),
        lead_id=str(data.get("lead_id") or ""),
        deal_id=str(data.get("deal_id") or ""),
        assigned_agent_id=str(data.get("assigned_agent_id") or data.get("assigned_to") or ""),
        created_by=str(data.get("created_by") or ""),
        status=status,
        priority=priority,
        due_at=float(due) if due not in (None, "") else None,
        completed_at=float(completed) if completed not in (None, "") else None,
        created_at=float(data.get("created_at") or 0.0),
        updated_at=float(data.get("updated_at") or data.get("created_at") or 0.0),
    )


def _activity_from_payload(data: dict) -> Interaction:
    type_raw = data.get("activity_type") or data.get("interaction_type") or InteractionType.NOTE.value
    try:
        itype = InteractionType(str(type_raw))
    except ValueError:
        itype = InteractionType.NOTE
    activity_id = str(data.get("activity_id") or data.get("interaction_id") or "")
    return Interaction(
        interaction_id=activity_id,
        customer_id=str(data.get("customer_id") or ""),
        lead_id=str(data.get("lead_id") or ""),
        deal_id=str(data.get("deal_id") or ""),
        task_id=str(data.get("task_id") or ""),
        interaction_type=itype,
        subject=str(data.get("subject") or ""),
        body=str(data.get("body") or ""),
        agent_id=str(data.get("agent_id") or ""),
        idempotency_key=str(data.get("idempotency_key") or ""),
        metadata=dict(data.get("metadata") or {}) if isinstance(data.get("metadata"), dict) else {},
        created_at=float(data.get("created_at") or 0.0),
    )


def _opt_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def _call_from_payload(data: dict) -> PhoneCall:
    return PhoneCall(
        call_id=str(data.get("call_id") or ""),
        customer_id=str(data.get("customer_id") or ""),
        lead_id=str(data.get("lead_id") or ""),
        deal_id=str(data.get("deal_id") or ""),
        agent_id=str(data.get("agent_id") or ""),
        direction=str(data.get("direction") or "outbound"),
        status=str(data.get("status") or "logged"),
        duration_sec=int(data.get("duration_sec") or 0),
        summary=str(data.get("summary") or data.get("notes") or ""),
        notes=str(data.get("notes") or data.get("summary") or ""),
        started_at=_opt_float(data.get("started_at")),
        ended_at=_opt_float(data.get("ended_at")),
        created_at=float(data.get("created_at") or 0.0),
        updated_at=float(data.get("updated_at") or data.get("created_at") or 0.0),
    )


def _email_from_payload(data: dict) -> EmailMessage:
    return EmailMessage(
        email_id=str(data.get("email_id") or ""),
        customer_id=str(data.get("customer_id") or ""),
        lead_id=str(data.get("lead_id") or ""),
        deal_id=str(data.get("deal_id") or ""),
        agent_id=str(data.get("agent_id") or ""),
        subject=str(data.get("subject") or ""),
        body=str(data.get("body") or ""),
        direction=str(data.get("direction") or "outbound"),
        status=str(data.get("status") or "logged"),
        sender=str(data.get("sender") or ""),
        recipient=str(data.get("recipient") or ""),
        created_at=float(data.get("created_at") or 0.0),
        updated_at=float(data.get("updated_at") or data.get("created_at") or 0.0),
    )


def _meeting_from_payload(data: dict) -> Meeting:
    return Meeting(
        meeting_id=str(data.get("meeting_id") or ""),
        customer_id=str(data.get("customer_id") or ""),
        lead_id=str(data.get("lead_id") or ""),
        deal_id=str(data.get("deal_id") or ""),
        agent_id=str(data.get("agent_id") or ""),
        title=str(data.get("title") or ""),
        description=str(data.get("description") or ""),
        scheduled_at=float(data.get("scheduled_at") or 0.0),
        duration_min=int(data.get("duration_min") or 30),
        location=str(data.get("location") or ""),
        status=str(data.get("status") or "scheduled"),
        completed=bool(data.get("completed")),
        created_at=float(data.get("created_at") or 0.0),
        updated_at=float(data.get("updated_at") or data.get("created_at") or 0.0),
    )


def _reminder_from_payload(data: dict) -> Reminder:
    trigger = data.get("trigger_at") if data.get("trigger_at") not in (None, "") else data.get("remind_at")
    return Reminder(
        reminder_id=str(data.get("reminder_id") or ""),
        task_id=str(data.get("task_id") or ""),
        customer_id=str(data.get("customer_id") or ""),
        lead_id=str(data.get("lead_id") or ""),
        deal_id=str(data.get("deal_id") or ""),
        title=str(data.get("title") or data.get("message") or ""),
        message=str(data.get("message") or data.get("title") or ""),
        assigned_agent_id=str(data.get("assigned_agent_id") or data.get("assigned_to") or ""),
        trigger_at=float(trigger or 0.0),
        status=str(data.get("status") or "pending"),
        triggered=bool(data.get("triggered")),
        created_at=float(data.get("created_at") or 0.0),
        updated_at=float(data.get("updated_at") or data.get("created_at") or 0.0),
    )


def _customer_from_payload(data: dict) -> CustomerProfile:
    return CustomerProfile(
        customer_id=str(data.get("customer_id") or ""),
        first_name=str(data.get("first_name") or ""),
        last_name=str(data.get("last_name") or ""),
        email=str(data.get("email") or ""),
        phone=str(data.get("phone") or ""),
        segment=str(data.get("segment") or "standard"),
        intent_score=float(data.get("intent_score") or 0.0),
        lifetime_value=float(data.get("lifetime_value") or 0.0),
        preferences=dict(data.get("preferences") or {}) if isinstance(data.get("preferences"), dict) else {},
        tags=list(data.get("tags") or []) if isinstance(data.get("tags"), list) else [],
        owner_agent_id=str(data.get("owner_agent_id") or ""),
        created_at=float(data.get("created_at") or 0.0),
    )


class CRMPersistence(Protocol):
    backend: str

    async def save_customer(self, profile: CustomerProfile, tenant_id: str | None = None) -> CustomerProfile: ...
    async def get_customer(self, customer_id: str, tenant_id: str | None = None) -> CustomerProfile | None: ...
    async def list_customers(self, tenant_id: str | None = None) -> list[CustomerProfile]: ...
    async def delete_customer(self, customer_id: str, tenant_id: str | None = None) -> bool: ...
    async def count_customers(self, tenant_id: str | None = None) -> int: ...

    async def save_lead(self, lead: CRMLead, tenant_id: str | None = None) -> CRMLead: ...
    async def get_lead(self, lead_id: str, tenant_id: str | None = None) -> CRMLead | None: ...
    async def list_leads(self, tenant_id: str | None = None) -> list[CRMLead]: ...
    async def delete_lead(self, lead_id: str, tenant_id: str | None = None) -> bool: ...
    async def count_leads(self, tenant_id: str | None = None) -> int: ...

    async def save_deal(self, deal: CRMDeal, tenant_id: str | None = None) -> CRMDeal: ...
    async def get_deal(self, deal_id: str, tenant_id: str | None = None) -> CRMDeal | None: ...
    async def list_deals(self, tenant_id: str | None = None) -> list[CRMDeal]: ...
    async def delete_deal(self, deal_id: str, tenant_id: str | None = None) -> bool: ...
    async def count_deals(self, tenant_id: str | None = None) -> int: ...

    async def save_task(self, task: CRMTask, tenant_id: str | None = None) -> CRMTask: ...
    async def get_task(self, task_id: str, tenant_id: str | None = None) -> CRMTask | None: ...
    async def list_tasks(self, tenant_id: str | None = None) -> list[CRMTask]: ...
    async def delete_task(self, task_id: str, tenant_id: str | None = None) -> bool: ...
    async def count_tasks(self, tenant_id: str | None = None) -> int: ...

    async def save_activity(self, activity: Interaction, tenant_id: str | None = None) -> Interaction: ...
    async def get_activity(self, activity_id: str, tenant_id: str | None = None) -> Interaction | None: ...
    async def get_activity_by_idempotency(self, key: str, tenant_id: str | None = None) -> Interaction | None: ...
    async def list_activities(self, tenant_id: str | None = None) -> list[Interaction]: ...
    async def delete_activity(self, activity_id: str, tenant_id: str | None = None) -> bool: ...
    async def count_activities(self, tenant_id: str | None = None) -> int: ...

    async def save_call(self, call: PhoneCall, tenant_id: str | None = None) -> PhoneCall: ...
    async def get_call(self, call_id: str, tenant_id: str | None = None) -> PhoneCall | None: ...
    async def list_calls(self, tenant_id: str | None = None) -> list[PhoneCall]: ...
    async def delete_call(self, call_id: str, tenant_id: str | None = None) -> bool: ...
    async def count_calls(self, tenant_id: str | None = None) -> int: ...

    async def save_email(self, email: EmailMessage, tenant_id: str | None = None) -> EmailMessage: ...
    async def get_email(self, email_id: str, tenant_id: str | None = None) -> EmailMessage | None: ...
    async def list_emails(self, tenant_id: str | None = None) -> list[EmailMessage]: ...
    async def delete_email(self, email_id: str, tenant_id: str | None = None) -> bool: ...
    async def count_emails(self, tenant_id: str | None = None) -> int: ...

    async def save_meeting(self, meeting: Meeting, tenant_id: str | None = None) -> Meeting: ...
    async def get_meeting(self, meeting_id: str, tenant_id: str | None = None) -> Meeting | None: ...
    async def list_meetings(self, tenant_id: str | None = None) -> list[Meeting]: ...
    async def delete_meeting(self, meeting_id: str, tenant_id: str | None = None) -> bool: ...
    async def count_meetings(self, tenant_id: str | None = None) -> int: ...

    async def save_reminder(self, reminder: Reminder, tenant_id: str | None = None) -> Reminder: ...
    async def get_reminder(self, reminder_id: str, tenant_id: str | None = None) -> Reminder | None: ...
    async def list_reminders(self, tenant_id: str | None = None) -> list[Reminder]: ...
    async def delete_reminder(self, reminder_id: str, tenant_id: str | None = None) -> bool: ...
    async def count_reminders(self, tenant_id: str | None = None) -> int: ...


def _tid(tenant_id: str | None) -> str:
    return tenant_id or current_crm_tenant()


class MemoryCRMPersistence:
    """Isolated in-process backend for AUTO_CRM_PERSISTENCE=memory (unit tests only).

    Production never uses this class. Collections are private so MarketplaceStore
    cannot act as a stale CRM shadow.
    """

    backend = "memory"

    def __init__(self) -> None:
        self._customers = EntityStore()
        self._leads = EntityStore()
        self._deals = EntityStore()
        self._tasks = EntityStore()
        self._activities = EntityStore()
        self._calls = EntityStore()
        self._emails = EntityStore()
        self._meetings = EntityStore()
        self._reminders = EntityStore()
        self._customer_tenants: dict[str, str] = {}
        self._lead_tenants: dict[str, str] = {}
        self._deal_tenants: dict[str, str] = {}
        self._task_tenants: dict[str, str] = {}
        self._activity_tenants: dict[str, str] = {}
        self._call_tenants: dict[str, str] = {}
        self._email_tenants: dict[str, str] = {}
        self._meeting_tenants: dict[str, str] = {}
        self._reminder_tenants: dict[str, str] = {}

    def _visible(self, entity_id: str, tenant_map: dict[str, str], tenant_id: str) -> bool:
        return tenant_map.get(entity_id, "default") == tenant_id

    async def save_customer(self, profile: CustomerProfile, tenant_id: str | None = None) -> CustomerProfile:
        tid = _tid(tenant_id)
        self._customer_tenants[profile.customer_id] = tid
        return self._customers.save(profile.customer_id, profile)

    async def get_customer(self, customer_id: str, tenant_id: str | None = None) -> CustomerProfile | None:
        tid = _tid(tenant_id)
        profile = self._customers.get(customer_id)
        if profile is None or not self._visible(customer_id, self._customer_tenants, tid):
            return None
        return profile

    async def list_customers(self, tenant_id: str | None = None) -> list[CustomerProfile]:
        tid = _tid(tenant_id)
        return [
            p
            for p in self._customers.list_all()
            if self._visible(p.customer_id, self._customer_tenants, tid)
        ]

    async def delete_customer(self, customer_id: str, tenant_id: str | None = None) -> bool:
        if await self.get_customer(customer_id, tenant_id) is None:
            return False
        self._customer_tenants.pop(customer_id, None)
        return self._customers.delete(customer_id)

    async def count_customers(self, tenant_id: str | None = None) -> int:
        return len(await self.list_customers(tenant_id))

    async def save_lead(self, lead: CRMLead, tenant_id: str | None = None) -> CRMLead:
        tid = _tid(tenant_id)
        self._lead_tenants[lead.lead_id] = tid
        return self._leads.save(lead.lead_id, lead)

    async def get_lead(self, lead_id: str, tenant_id: str | None = None) -> CRMLead | None:
        tid = _tid(tenant_id)
        lead = self._leads.get(lead_id)
        if lead is None or not self._visible(lead_id, self._lead_tenants, tid):
            return None
        return lead

    async def list_leads(self, tenant_id: str | None = None) -> list[CRMLead]:
        tid = _tid(tenant_id)
        return [lead for lead in self._leads.list_all() if self._visible(lead.lead_id, self._lead_tenants, tid)]

    async def delete_lead(self, lead_id: str, tenant_id: str | None = None) -> bool:
        if await self.get_lead(lead_id, tenant_id) is None:
            return False
        self._lead_tenants.pop(lead_id, None)
        return self._leads.delete(lead_id)

    async def count_leads(self, tenant_id: str | None = None) -> int:
        return len(await self.list_leads(tenant_id))

    async def save_deal(self, deal: CRMDeal, tenant_id: str | None = None) -> CRMDeal:
        tid = _tid(tenant_id)
        self._deal_tenants[deal.deal_id] = tid
        return self._deals.save(deal.deal_id, deal)

    async def get_deal(self, deal_id: str, tenant_id: str | None = None) -> CRMDeal | None:
        tid = _tid(tenant_id)
        deal = self._deals.get(deal_id)
        if deal is None or not self._visible(deal_id, self._deal_tenants, tid):
            return None
        return deal

    async def list_deals(self, tenant_id: str | None = None) -> list[CRMDeal]:
        tid = _tid(tenant_id)
        return [d for d in self._deals.list_all() if self._visible(d.deal_id, self._deal_tenants, tid)]

    async def delete_deal(self, deal_id: str, tenant_id: str | None = None) -> bool:
        if await self.get_deal(deal_id, tenant_id) is None:
            return False
        self._deal_tenants.pop(deal_id, None)
        return self._deals.delete(deal_id)

    async def count_deals(self, tenant_id: str | None = None) -> int:
        return len(await self.list_deals(tenant_id))

    async def save_task(self, task: CRMTask, tenant_id: str | None = None) -> CRMTask:
        tid = _tid(tenant_id)
        self._task_tenants[task.task_id] = tid
        return self._tasks.save(task.task_id, task)

    async def get_task(self, task_id: str, tenant_id: str | None = None) -> CRMTask | None:
        tid = _tid(tenant_id)
        task = self._tasks.get(task_id)
        if task is None or not self._visible(task_id, self._task_tenants, tid):
            return None
        return task

    async def list_tasks(self, tenant_id: str | None = None) -> list[CRMTask]:
        tid = _tid(tenant_id)
        return [t for t in self._tasks.list_all() if self._visible(t.task_id, self._task_tenants, tid)]

    async def delete_task(self, task_id: str, tenant_id: str | None = None) -> bool:
        if await self.get_task(task_id, tenant_id) is None:
            return False
        self._task_tenants.pop(task_id, None)
        return self._tasks.delete(task_id)

    async def count_tasks(self, tenant_id: str | None = None) -> int:
        return len(await self.list_tasks(tenant_id))

    async def save_activity(self, activity: Interaction, tenant_id: str | None = None) -> Interaction:
        tid = _tid(tenant_id)
        self._activity_tenants[activity.interaction_id] = tid
        return self._activities.save(activity.interaction_id, activity)

    async def get_activity(self, activity_id: str, tenant_id: str | None = None) -> Interaction | None:
        tid = _tid(tenant_id)
        item = self._activities.get(activity_id)
        if item is None or not self._visible(activity_id, self._activity_tenants, tid):
            return None
        return item

    async def get_activity_by_idempotency(self, key: str, tenant_id: str | None = None) -> Interaction | None:
        if not key:
            return None
        for item in await self.list_activities(tenant_id):
            if item.idempotency_key == key:
                return item
        return None

    async def list_activities(self, tenant_id: str | None = None) -> list[Interaction]:
        tid = _tid(tenant_id)
        return [
            i
            for i in self._activities.list_all()
            if self._visible(i.interaction_id, self._activity_tenants, tid)
        ]

    async def delete_activity(self, activity_id: str, tenant_id: str | None = None) -> bool:
        if await self.get_activity(activity_id, tenant_id) is None:
            return False
        self._activity_tenants.pop(activity_id, None)
        return self._activities.delete(activity_id)

    async def count_activities(self, tenant_id: str | None = None) -> int:
        return len(await self.list_activities(tenant_id))

    async def save_call(self, call: PhoneCall, tenant_id: str | None = None) -> PhoneCall:
        tid = _tid(tenant_id)
        self._call_tenants[call.call_id] = tid
        return self._calls.save(call.call_id, call)

    async def get_call(self, call_id: str, tenant_id: str | None = None) -> PhoneCall | None:
        tid = _tid(tenant_id)
        item = self._calls.get(call_id)
        if item is None or not self._visible(call_id, self._call_tenants, tid):
            return None
        return item

    async def list_calls(self, tenant_id: str | None = None) -> list[PhoneCall]:
        tid = _tid(tenant_id)
        return [c for c in self._calls.list_all() if self._visible(c.call_id, self._call_tenants, tid)]

    async def delete_call(self, call_id: str, tenant_id: str | None = None) -> bool:
        if await self.get_call(call_id, tenant_id) is None:
            return False
        self._call_tenants.pop(call_id, None)
        return self._calls.delete(call_id)

    async def count_calls(self, tenant_id: str | None = None) -> int:
        return len(await self.list_calls(tenant_id))

    async def save_email(self, email: EmailMessage, tenant_id: str | None = None) -> EmailMessage:
        tid = _tid(tenant_id)
        self._email_tenants[email.email_id] = tid
        return self._emails.save(email.email_id, email)

    async def get_email(self, email_id: str, tenant_id: str | None = None) -> EmailMessage | None:
        tid = _tid(tenant_id)
        item = self._emails.get(email_id)
        if item is None or not self._visible(email_id, self._email_tenants, tid):
            return None
        return item

    async def list_emails(self, tenant_id: str | None = None) -> list[EmailMessage]:
        tid = _tid(tenant_id)
        return [e for e in self._emails.list_all() if self._visible(e.email_id, self._email_tenants, tid)]

    async def delete_email(self, email_id: str, tenant_id: str | None = None) -> bool:
        if await self.get_email(email_id, tenant_id) is None:
            return False
        self._email_tenants.pop(email_id, None)
        return self._emails.delete(email_id)

    async def count_emails(self, tenant_id: str | None = None) -> int:
        return len(await self.list_emails(tenant_id))

    async def save_meeting(self, meeting: Meeting, tenant_id: str | None = None) -> Meeting:
        tid = _tid(tenant_id)
        self._meeting_tenants[meeting.meeting_id] = tid
        return self._meetings.save(meeting.meeting_id, meeting)

    async def get_meeting(self, meeting_id: str, tenant_id: str | None = None) -> Meeting | None:
        tid = _tid(tenant_id)
        item = self._meetings.get(meeting_id)
        if item is None or not self._visible(meeting_id, self._meeting_tenants, tid):
            return None
        return item

    async def list_meetings(self, tenant_id: str | None = None) -> list[Meeting]:
        tid = _tid(tenant_id)
        return [m for m in self._meetings.list_all() if self._visible(m.meeting_id, self._meeting_tenants, tid)]

    async def delete_meeting(self, meeting_id: str, tenant_id: str | None = None) -> bool:
        if await self.get_meeting(meeting_id, tenant_id) is None:
            return False
        self._meeting_tenants.pop(meeting_id, None)
        return self._meetings.delete(meeting_id)

    async def count_meetings(self, tenant_id: str | None = None) -> int:
        return len(await self.list_meetings(tenant_id))

    async def save_reminder(self, reminder: Reminder, tenant_id: str | None = None) -> Reminder:
        tid = _tid(tenant_id)
        self._reminder_tenants[reminder.reminder_id] = tid
        return self._reminders.save(reminder.reminder_id, reminder)

    async def get_reminder(self, reminder_id: str, tenant_id: str | None = None) -> Reminder | None:
        tid = _tid(tenant_id)
        item = self._reminders.get(reminder_id)
        if item is None or not self._visible(reminder_id, self._reminder_tenants, tid):
            return None
        return item

    async def list_reminders(self, tenant_id: str | None = None) -> list[Reminder]:
        tid = _tid(tenant_id)
        return [r for r in self._reminders.list_all() if self._visible(r.reminder_id, self._reminder_tenants, tid)]

    async def delete_reminder(self, reminder_id: str, tenant_id: str | None = None) -> bool:
        if await self.get_reminder(reminder_id, tenant_id) is None:
            return False
        self._reminder_tenants.pop(reminder_id, None)
        return self._reminders.delete(reminder_id)

    async def count_reminders(self, tenant_id: str | None = None) -> int:
        return len(await self.list_reminders(tenant_id))


class PostgresCRMPersistence:
    """Production backend: PostgreSQL is the durable source of truth."""

    backend = "postgres"

    async def save_customer(self, profile: CustomerProfile, tenant_id: str | None = None) -> CustomerProfile:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            await repo.upsert_customer(tid, profile.to_dict())
        return profile

    async def get_customer(self, customer_id: str, tenant_id: str | None = None) -> CustomerProfile | None:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            data = await repo.get_customer(tid, customer_id)
        return _customer_from_payload(data) if data else None

    async def list_customers(self, tenant_id: str | None = None) -> list[CustomerProfile]:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            rows = await repo.list_customers(tid)
        return [_customer_from_payload(row) for row in rows]

    async def delete_customer(self, customer_id: str, tenant_id: str | None = None) -> bool:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            return await repo.delete_customer(tid, customer_id)

    async def count_customers(self, tenant_id: str | None = None) -> int:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            return await repo.count_customers(tid)

    async def save_lead(self, lead: CRMLead, tenant_id: str | None = None) -> CRMLead:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            await repo.upsert_lead(tid, lead.to_dict())
        return lead

    async def get_lead(self, lead_id: str, tenant_id: str | None = None) -> CRMLead | None:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            data = await repo.get_lead(tid, lead_id)
        return _lead_from_payload(data) if data else None

    async def list_leads(self, tenant_id: str | None = None) -> list[CRMLead]:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            rows = await repo.list_leads(tid)
        return [_lead_from_payload(row) for row in rows]

    async def delete_lead(self, lead_id: str, tenant_id: str | None = None) -> bool:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            return await repo.delete_lead(tid, lead_id)

    async def count_leads(self, tenant_id: str | None = None) -> int:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            return await repo.count_leads(tid)

    async def save_deal(self, deal: CRMDeal, tenant_id: str | None = None) -> CRMDeal:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            await repo.upsert_deal(tid, deal.to_dict())
        return deal

    async def get_deal(self, deal_id: str, tenant_id: str | None = None) -> CRMDeal | None:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            data = await repo.get_deal(tid, deal_id)
        return _deal_from_payload(data) if data else None

    async def list_deals(self, tenant_id: str | None = None) -> list[CRMDeal]:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            rows = await repo.list_deals(tid)
        return [_deal_from_payload(row) for row in rows]

    async def delete_deal(self, deal_id: str, tenant_id: str | None = None) -> bool:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            return await repo.delete_deal(tid, deal_id)

    async def count_deals(self, tenant_id: str | None = None) -> int:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            return await repo.count_deals(tid)


    async def save_task(self, task: CRMTask, tenant_id: str | None = None) -> CRMTask:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            await repo.upsert_task(tid, task.to_dict())
        return task

    async def get_task(self, task_id: str, tenant_id: str | None = None) -> CRMTask | None:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            data = await repo.get_task(tid, task_id)
        return _task_from_payload(data) if data else None

    async def list_tasks(self, tenant_id: str | None = None) -> list[CRMTask]:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            rows = await repo.list_tasks(tid)
        return [_task_from_payload(row) for row in rows]

    async def delete_task(self, task_id: str, tenant_id: str | None = None) -> bool:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            return await repo.delete_task(tid, task_id)

    async def count_tasks(self, tenant_id: str | None = None) -> int:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            return await repo.count_tasks(tid)

    async def save_activity(self, activity: Interaction, tenant_id: str | None = None) -> Interaction:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            await repo.upsert_activity(tid, activity.to_dict())
        return activity

    async def get_activity(self, activity_id: str, tenant_id: str | None = None) -> Interaction | None:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            data = await repo.get_activity(tid, activity_id)
        return _activity_from_payload(data) if data else None

    async def get_activity_by_idempotency(self, key: str, tenant_id: str | None = None) -> Interaction | None:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        if not key:
            return None
        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            data = await repo.get_activity_by_idempotency(tid, key)
        return _activity_from_payload(data) if data else None

    async def list_activities(self, tenant_id: str | None = None) -> list[Interaction]:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            rows = await repo.list_activities(tid)
        return [_activity_from_payload(row) for row in rows]

    async def delete_activity(self, activity_id: str, tenant_id: str | None = None) -> bool:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            return await repo.delete_activity(tid, activity_id)

    async def count_activities(self, tenant_id: str | None = None) -> int:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            return await repo.count_activities(tid)

    async def save_call(self, call: PhoneCall, tenant_id: str | None = None) -> PhoneCall:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            await repo.upsert_call(tid, call.to_dict())
        return call

    async def get_call(self, call_id: str, tenant_id: str | None = None) -> PhoneCall | None:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            data = await repo.get_call(tid, call_id)
        return _call_from_payload(data) if data else None

    async def list_calls(self, tenant_id: str | None = None) -> list[PhoneCall]:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            rows = await repo.list_calls(tid)
        return [_call_from_payload(row) for row in rows]

    async def delete_call(self, call_id: str, tenant_id: str | None = None) -> bool:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            return await repo.delete_call(tid, call_id)

    async def count_calls(self, tenant_id: str | None = None) -> int:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            return await repo.count_calls(tid)

    async def save_email(self, email: EmailMessage, tenant_id: str | None = None) -> EmailMessage:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            await repo.upsert_email(tid, email.to_dict())
        return email

    async def get_email(self, email_id: str, tenant_id: str | None = None) -> EmailMessage | None:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            data = await repo.get_email(tid, email_id)
        return _email_from_payload(data) if data else None

    async def list_emails(self, tenant_id: str | None = None) -> list[EmailMessage]:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            rows = await repo.list_emails(tid)
        return [_email_from_payload(row) for row in rows]

    async def delete_email(self, email_id: str, tenant_id: str | None = None) -> bool:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            return await repo.delete_email(tid, email_id)

    async def count_emails(self, tenant_id: str | None = None) -> int:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            return await repo.count_emails(tid)

    async def save_meeting(self, meeting: Meeting, tenant_id: str | None = None) -> Meeting:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            await repo.upsert_meeting(tid, meeting.to_dict())
        return meeting

    async def get_meeting(self, meeting_id: str, tenant_id: str | None = None) -> Meeting | None:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            data = await repo.get_meeting(tid, meeting_id)
        return _meeting_from_payload(data) if data else None

    async def list_meetings(self, tenant_id: str | None = None) -> list[Meeting]:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            rows = await repo.list_meetings(tid)
        return [_meeting_from_payload(row) for row in rows]

    async def delete_meeting(self, meeting_id: str, tenant_id: str | None = None) -> bool:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            return await repo.delete_meeting(tid, meeting_id)

    async def count_meetings(self, tenant_id: str | None = None) -> int:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            return await repo.count_meetings(tid)

    async def save_reminder(self, reminder: Reminder, tenant_id: str | None = None) -> Reminder:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            await repo.upsert_reminder(tid, reminder.to_dict())
        return reminder

    async def get_reminder(self, reminder_id: str, tenant_id: str | None = None) -> Reminder | None:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            data = await repo.get_reminder(tid, reminder_id)
        return _reminder_from_payload(data) if data else None

    async def list_reminders(self, tenant_id: str | None = None) -> list[Reminder]:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            rows = await repo.list_reminders(tid)
        return [_reminder_from_payload(row) for row in rows]

    async def delete_reminder(self, reminder_id: str, tenant_id: str | None = None) -> bool:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            return await repo.delete_reminder(tid, reminder_id)

    async def count_reminders(self, tenant_id: str | None = None) -> int:
        from database.session import get_session
        from repositories.auto_marketplace_crm_repository import AutoMarketplaceCrmRepository

        tid = _tid(tenant_id)
        async with get_session() as session:
            repo = AutoMarketplaceCrmRepository(session)
            return await repo.count_reminders(tid)


_persist: CRMPersistence | None = None


def get_crm_persistence() -> CRMPersistence:
    global _persist
    mode = crm_persistence_mode()
    if _persist is not None and _persist.backend == mode:
        return _persist
    if mode == "memory":
        _persist = MemoryCRMPersistence()
    else:
        _persist = PostgresCRMPersistence()
    return _persist


def reset_crm_persistence() -> None:
    """Drop the cached backend so tests can switch memory/postgres."""
    global _persist
    _persist = None
    from applications.auto_marketplace.crm.metrics import crm_metrics

    crm_metrics.reset()
