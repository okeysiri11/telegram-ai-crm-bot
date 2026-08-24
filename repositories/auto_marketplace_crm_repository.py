"""Auto Marketplace Web CRM repository — tenant-scoped PostgreSQL access.

Uses SQLAlchemy Core (table inserts/selects) so first access does not
configure the full shared declarative mapper registry.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.auto_marketplace_crm import (
    AutoMarketplaceCrmActivity,
    AutoMarketplaceCrmCall,
    AutoMarketplaceCrmCustomer,
    AutoMarketplaceCrmDeal,
    AutoMarketplaceCrmEmail,
    AutoMarketplaceCrmLead,
    AutoMarketplaceCrmMeeting,
    AutoMarketplaceCrmReminder,
    AutoMarketplaceCrmTask,
)

_CUSTOMERS = AutoMarketplaceCrmCustomer.__table__
_LEADS = AutoMarketplaceCrmLead.__table__
_DEALS = AutoMarketplaceCrmDeal.__table__
_TASKS = AutoMarketplaceCrmTask.__table__
_ACTIVITIES = AutoMarketplaceCrmActivity.__table__
_CALLS = AutoMarketplaceCrmCall.__table__
_EMAILS = AutoMarketplaceCrmEmail.__table__
_MEETINGS = AutoMarketplaceCrmMeeting.__table__
_REMINDERS = AutoMarketplaceCrmReminder.__table__


def _payload_from_row(row: Any) -> dict[str, Any] | None:
    if row is None:
        return None
    mapping = dict(row)
    payload = dict(mapping.get("payload") or {})
    payload["tenant_id"] = mapping.get("tenant_id")
    return payload


class AutoMarketplaceCrmRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _fetch_one(self, stmt) -> dict[str, Any] | None:
        result = await self._session.execute(stmt)
        return _payload_from_row(result.mappings().first())

    async def _fetch_all(self, stmt) -> list[dict[str, Any]]:
        result = await self._session.execute(stmt)
        items: list[dict[str, Any]] = []
        for row in result.mappings().all():
            payload = _payload_from_row(row)
            if payload is not None:
                items.append(payload)
        return items

    # --- customers -----------------------------------------------------------

    async def upsert_customer(self, tenant_id: str, data: dict[str, Any]) -> dict[str, Any]:
        customer_id = str(data["customer_id"])
        existing = await self._session.execute(
            select(_CUSTOMERS).where(_CUSTOMERS.c.customer_id == customer_id)
        )
        row = existing.mappings().first()
        if row is not None and row["tenant_id"] != tenant_id:
            payload = _payload_from_row(row)
            return payload or dict(data)
        values = {
            "tenant_id": tenant_id,
            "first_name": str(data.get("first_name") or ""),
            "last_name": str(data.get("last_name") or ""),
            "email": str(data.get("email") or ""),
            "phone": str(data.get("phone") or ""),
            "segment": str(data.get("segment") or "standard"),
            "intent_score": float(data.get("intent_score") or 0.0),
            "lifetime_value": float(data.get("lifetime_value") or 0.0),
            "owner_agent_id": str(data.get("owner_agent_id") or ""),
            "created_ts": float(data.get("created_at") or 0.0),
            "payload": dict(data),
        }
        if row is None:
            await self._session.execute(insert(_CUSTOMERS).values(customer_id=customer_id, **values))
        else:
            await self._session.execute(
                update(_CUSTOMERS).where(_CUSTOMERS.c.customer_id == customer_id).values(**values)
            )
        await self._session.flush()
        found = await self.get_customer(tenant_id, customer_id)
        return found or {**dict(data), "tenant_id": tenant_id}

    async def get_customer(self, tenant_id: str, customer_id: str) -> dict[str, Any] | None:
        return await self._fetch_one(
            select(_CUSTOMERS).where(
                _CUSTOMERS.c.customer_id == customer_id,
                _CUSTOMERS.c.tenant_id == tenant_id,
            )
        )

    async def list_customers(self, tenant_id: str) -> list[dict[str, Any]]:
        return await self._fetch_all(select(_CUSTOMERS).where(_CUSTOMERS.c.tenant_id == tenant_id))

    async def delete_customer(self, tenant_id: str, customer_id: str) -> bool:
        result = await self._session.execute(
            delete(_CUSTOMERS).where(
                _CUSTOMERS.c.customer_id == customer_id,
                _CUSTOMERS.c.tenant_id == tenant_id,
            )
        )
        await self._session.flush()
        return bool(result.rowcount)

    async def count_customers(self, tenant_id: str) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(_CUSTOMERS).where(_CUSTOMERS.c.tenant_id == tenant_id)
        )
        return int(result.scalar_one())

    # --- leads ---------------------------------------------------------------

    async def upsert_lead(self, tenant_id: str, data: dict[str, Any]) -> dict[str, Any]:
        lead_id = str(data["lead_id"])
        existing = await self._session.execute(select(_LEADS).where(_LEADS.c.lead_id == lead_id))
        row = existing.mappings().first()
        if row is not None and row["tenant_id"] != tenant_id:
            payload = _payload_from_row(row)
            return payload or dict(data)
        qualified = data.get("qualified_at")
        values = {
            "tenant_id": tenant_id,
            "customer_id": str(data.get("customer_id") or ""),
            "vehicle_id": str(data.get("vehicle_id") or ""),
            "dealer_id": str(data.get("dealer_id") or ""),
            "source": str(data.get("source") or "web"),
            "status": str(data.get("status") or "new"),
            "score": float(data.get("score") or 0.0),
            "assigned_agent_id": str(data.get("assigned_agent_id") or ""),
            "notes": str(data.get("notes") or ""),
            "created_ts": float(data.get("created_at") or 0.0),
            "qualified_at": float(qualified) if qualified is not None else None,
            "payload": dict(data),
        }
        if row is None:
            await self._session.execute(insert(_LEADS).values(lead_id=lead_id, **values))
        else:
            await self._session.execute(update(_LEADS).where(_LEADS.c.lead_id == lead_id).values(**values))
        await self._session.flush()
        found = await self.get_lead(tenant_id, lead_id)
        return found or {**dict(data), "tenant_id": tenant_id}

    async def get_lead(self, tenant_id: str, lead_id: str) -> dict[str, Any] | None:
        return await self._fetch_one(
            select(_LEADS).where(_LEADS.c.lead_id == lead_id, _LEADS.c.tenant_id == tenant_id)
        )

    async def list_leads(self, tenant_id: str) -> list[dict[str, Any]]:
        return await self._fetch_all(select(_LEADS).where(_LEADS.c.tenant_id == tenant_id))

    async def delete_lead(self, tenant_id: str, lead_id: str) -> bool:
        result = await self._session.execute(
            delete(_LEADS).where(_LEADS.c.lead_id == lead_id, _LEADS.c.tenant_id == tenant_id)
        )
        await self._session.flush()
        return bool(result.rowcount)

    async def count_leads(self, tenant_id: str) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(_LEADS).where(_LEADS.c.tenant_id == tenant_id)
        )
        return int(result.scalar_one())

    # --- deals ---------------------------------------------------------------

    async def upsert_deal(self, tenant_id: str, data: dict[str, Any]) -> dict[str, Any]:
        deal_id = str(data["deal_id"])
        existing = await self._session.execute(select(_DEALS).where(_DEALS.c.deal_id == deal_id))
        row = existing.mappings().first()
        if row is not None and row["tenant_id"] != tenant_id:
            payload = _payload_from_row(row)
            return payload or dict(data)
        closed = data.get("closed_at")
        values = {
            "tenant_id": tenant_id,
            "opportunity_id": str(data.get("opportunity_id") or ""),
            "customer_id": str(data.get("customer_id") or ""),
            "dealer_id": str(data.get("dealer_id") or ""),
            "vehicle_id": str(data.get("vehicle_id") or ""),
            "stage": str(data.get("stage") or "prospect"),
            "amount": float(data.get("amount") or 0.0),
            "probability": float(data.get("probability") or 0.1),
            "win": data.get("win"),
            "owner_agent_id": str(data.get("owner_agent_id") or ""),
            "created_ts": float(data.get("created_at") or 0.0),
            "closed_at": float(closed) if closed is not None else None,
            "payload": dict(data),
        }
        if row is None:
            await self._session.execute(insert(_DEALS).values(deal_id=deal_id, **values))
        else:
            await self._session.execute(update(_DEALS).where(_DEALS.c.deal_id == deal_id).values(**values))
        await self._session.flush()
        found = await self.get_deal(tenant_id, deal_id)
        return found or {**dict(data), "tenant_id": tenant_id}

    async def get_deal(self, tenant_id: str, deal_id: str) -> dict[str, Any] | None:
        return await self._fetch_one(
            select(_DEALS).where(_DEALS.c.deal_id == deal_id, _DEALS.c.tenant_id == tenant_id)
        )

    async def list_deals(self, tenant_id: str) -> list[dict[str, Any]]:
        return await self._fetch_all(select(_DEALS).where(_DEALS.c.tenant_id == tenant_id))

    async def delete_deal(self, tenant_id: str, deal_id: str) -> bool:
        result = await self._session.execute(
            delete(_DEALS).where(_DEALS.c.deal_id == deal_id, _DEALS.c.tenant_id == tenant_id)
        )
        await self._session.flush()
        return bool(result.rowcount)

    async def count_deals(self, tenant_id: str) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(_DEALS).where(_DEALS.c.tenant_id == tenant_id)
        )
        return int(result.scalar_one())

    # --- tasks ---------------------------------------------------------------

    async def upsert_task(self, tenant_id: str, data: dict[str, Any]) -> dict[str, Any]:
        task_id = str(data["task_id"])
        existing = await self._session.execute(select(_TASKS).where(_TASKS.c.task_id == task_id))
        row = existing.mappings().first()
        if row is not None and row["tenant_id"] != tenant_id:
            payload = _payload_from_row(row)
            return payload or dict(data)
        due = data.get("due_at")
        completed = data.get("completed_at")
        values = {
            "tenant_id": tenant_id,
            "title": str(data.get("title") or ""),
            "description": str(data.get("description") or ""),
            "status": str(data.get("status") or "pending"),
            "priority": str(data.get("priority") or "normal"),
            "customer_id": str(data.get("customer_id") or ""),
            "lead_id": str(data.get("lead_id") or ""),
            "deal_id": str(data.get("deal_id") or ""),
            "assigned_agent_id": str(data.get("assigned_agent_id") or data.get("assigned_to") or ""),
            "created_by": str(data.get("created_by") or ""),
            "due_at": float(due) if due is not None and due != "" else None,
            "completed_at": float(completed) if completed is not None and completed != "" else None,
            "created_ts": float(data.get("created_at") or 0.0),
            "payload": dict(data),
        }
        if row is None:
            await self._session.execute(insert(_TASKS).values(task_id=task_id, **values))
        else:
            await self._session.execute(update(_TASKS).where(_TASKS.c.task_id == task_id).values(**values))
        await self._session.flush()
        found = await self.get_task(tenant_id, task_id)
        return found or {**dict(data), "tenant_id": tenant_id}

    async def get_task(self, tenant_id: str, task_id: str) -> dict[str, Any] | None:
        return await self._fetch_one(
            select(_TASKS).where(_TASKS.c.task_id == task_id, _TASKS.c.tenant_id == tenant_id)
        )

    async def list_tasks(self, tenant_id: str) -> list[dict[str, Any]]:
        return await self._fetch_all(select(_TASKS).where(_TASKS.c.tenant_id == tenant_id))

    async def delete_task(self, tenant_id: str, task_id: str) -> bool:
        result = await self._session.execute(
            delete(_TASKS).where(_TASKS.c.task_id == task_id, _TASKS.c.tenant_id == tenant_id)
        )
        await self._session.flush()
        return bool(result.rowcount)

    async def count_tasks(self, tenant_id: str) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(_TASKS).where(_TASKS.c.tenant_id == tenant_id)
        )
        return int(result.scalar_one())

    # --- activities ----------------------------------------------------------

    async def upsert_activity(self, tenant_id: str, data: dict[str, Any]) -> dict[str, Any]:
        activity_id = str(data.get("activity_id") or data.get("interaction_id") or "")
        existing = await self._session.execute(
            select(_ACTIVITIES).where(_ACTIVITIES.c.activity_id == activity_id)
        )
        row = existing.mappings().first()
        if row is not None and row["tenant_id"] != tenant_id:
            payload = _payload_from_row(row)
            return payload or dict(data)
        values = {
            "tenant_id": tenant_id,
            "activity_type": str(data.get("activity_type") or data.get("interaction_type") or "note"),
            "customer_id": str(data.get("customer_id") or ""),
            "lead_id": str(data.get("lead_id") or ""),
            "deal_id": str(data.get("deal_id") or ""),
            "task_id": str(data.get("task_id") or ""),
            "agent_id": str(data.get("agent_id") or ""),
            "subject": str(data.get("subject") or ""),
            "body": str(data.get("body") or ""),
            "idempotency_key": str(data.get("idempotency_key") or ""),
            "created_ts": float(data.get("created_at") or 0.0),
            "payload": dict(data),
        }
        if row is None:
            await self._session.execute(insert(_ACTIVITIES).values(activity_id=activity_id, **values))
        else:
            await self._session.execute(
                update(_ACTIVITIES).where(_ACTIVITIES.c.activity_id == activity_id).values(**values)
            )
        await self._session.flush()
        found = await self.get_activity(tenant_id, activity_id)
        return found or {**dict(data), "tenant_id": tenant_id}

    async def get_activity(self, tenant_id: str, activity_id: str) -> dict[str, Any] | None:
        return await self._fetch_one(
            select(_ACTIVITIES).where(
                _ACTIVITIES.c.activity_id == activity_id,
                _ACTIVITIES.c.tenant_id == tenant_id,
            )
        )

    async def get_activity_by_idempotency(self, tenant_id: str, idempotency_key: str) -> dict[str, Any] | None:
        if not idempotency_key:
            return None
        return await self._fetch_one(
            select(_ACTIVITIES).where(
                _ACTIVITIES.c.tenant_id == tenant_id,
                _ACTIVITIES.c.idempotency_key == idempotency_key,
            )
        )

    async def list_activities(self, tenant_id: str) -> list[dict[str, Any]]:
        return await self._fetch_all(select(_ACTIVITIES).where(_ACTIVITIES.c.tenant_id == tenant_id))

    async def delete_activity(self, tenant_id: str, activity_id: str) -> bool:
        result = await self._session.execute(
            delete(_ACTIVITIES).where(
                _ACTIVITIES.c.activity_id == activity_id,
                _ACTIVITIES.c.tenant_id == tenant_id,
            )
        )
        await self._session.flush()
        return bool(result.rowcount)

    async def count_activities(self, tenant_id: str) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(_ACTIVITIES).where(_ACTIVITIES.c.tenant_id == tenant_id)
        )
        return int(result.scalar_one())

    async def _upsert_row(
        self,
        table,
        pk_name: str,
        pk_value: str,
        tenant_id: str,
        values: dict[str, Any],
        data: dict[str, Any],
    ) -> dict[str, Any]:
        pk_col = getattr(table.c, pk_name)
        existing = await self._session.execute(select(table).where(pk_col == pk_value))
        row = existing.mappings().first()
        if row is not None and row["tenant_id"] != tenant_id:
            payload = _payload_from_row(row)
            return payload or dict(data)
        if row is None:
            await self._session.execute(insert(table).values(**{pk_name: pk_value}, **values))
        else:
            await self._session.execute(update(table).where(pk_col == pk_value).values(**values))
        await self._session.flush()
        found = await self._fetch_one(select(table).where(pk_col == pk_value, table.c.tenant_id == tenant_id))
        return found or {**dict(data), "tenant_id": tenant_id}

    async def _delete_row(self, table, pk_name: str, pk_value: str, tenant_id: str) -> bool:
        result = await self._session.execute(
            delete(table).where(getattr(table.c, pk_name) == pk_value, table.c.tenant_id == tenant_id)
        )
        await self._session.flush()
        return bool(result.rowcount)

    async def _count_rows(self, table, tenant_id: str) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(table).where(table.c.tenant_id == tenant_id)
        )
        return int(result.scalar_one())

    async def upsert_call(self, tenant_id: str, data: dict[str, Any]) -> dict[str, Any]:
        call_id = str(data["call_id"])
        started = data.get("started_at")
        ended = data.get("ended_at")
        values = {
            "tenant_id": tenant_id,
            "customer_id": str(data.get("customer_id") or ""),
            "lead_id": str(data.get("lead_id") or ""),
            "deal_id": str(data.get("deal_id") or ""),
            "agent_id": str(data.get("agent_id") or ""),
            "direction": str(data.get("direction") or "outbound"),
            "status": str(data.get("status") or "logged"),
            "duration_sec": int(data.get("duration_sec") or 0),
            "summary": str(data.get("summary") or data.get("notes") or ""),
            "started_at": float(started) if started not in (None, "") else None,
            "ended_at": float(ended) if ended not in (None, "") else None,
            "created_ts": float(data.get("created_at") or 0.0),
            "payload": dict(data),
        }
        return await self._upsert_row(_CALLS, "call_id", call_id, tenant_id, values, data)

    async def get_call(self, tenant_id: str, call_id: str) -> dict[str, Any] | None:
        return await self._fetch_one(select(_CALLS).where(_CALLS.c.call_id == call_id, _CALLS.c.tenant_id == tenant_id))

    async def list_calls(self, tenant_id: str) -> list[dict[str, Any]]:
        return await self._fetch_all(select(_CALLS).where(_CALLS.c.tenant_id == tenant_id))

    async def delete_call(self, tenant_id: str, call_id: str) -> bool:
        return await self._delete_row(_CALLS, "call_id", call_id, tenant_id)

    async def count_calls(self, tenant_id: str) -> int:
        return await self._count_rows(_CALLS, tenant_id)

    async def upsert_email(self, tenant_id: str, data: dict[str, Any]) -> dict[str, Any]:
        email_id = str(data["email_id"])
        values = {
            "tenant_id": tenant_id,
            "customer_id": str(data.get("customer_id") or ""),
            "lead_id": str(data.get("lead_id") or ""),
            "deal_id": str(data.get("deal_id") or ""),
            "agent_id": str(data.get("agent_id") or ""),
            "subject": str(data.get("subject") or ""),
            "body": str(data.get("body") or ""),
            "direction": str(data.get("direction") or "outbound"),
            "status": str(data.get("status") or "logged"),
            "sender": str(data.get("sender") or ""),
            "recipient": str(data.get("recipient") or ""),
            "created_ts": float(data.get("created_at") or 0.0),
            "payload": dict(data),
        }
        return await self._upsert_row(_EMAILS, "email_id", email_id, tenant_id, values, data)

    async def get_email(self, tenant_id: str, email_id: str) -> dict[str, Any] | None:
        return await self._fetch_one(
            select(_EMAILS).where(_EMAILS.c.email_id == email_id, _EMAILS.c.tenant_id == tenant_id)
        )

    async def list_emails(self, tenant_id: str) -> list[dict[str, Any]]:
        return await self._fetch_all(select(_EMAILS).where(_EMAILS.c.tenant_id == tenant_id))

    async def delete_email(self, tenant_id: str, email_id: str) -> bool:
        return await self._delete_row(_EMAILS, "email_id", email_id, tenant_id)

    async def count_emails(self, tenant_id: str) -> int:
        return await self._count_rows(_EMAILS, tenant_id)

    async def upsert_meeting(self, tenant_id: str, data: dict[str, Any]) -> dict[str, Any]:
        meeting_id = str(data["meeting_id"])
        values = {
            "tenant_id": tenant_id,
            "customer_id": str(data.get("customer_id") or ""),
            "lead_id": str(data.get("lead_id") or ""),
            "deal_id": str(data.get("deal_id") or ""),
            "agent_id": str(data.get("agent_id") or ""),
            "title": str(data.get("title") or ""),
            "description": str(data.get("description") or ""),
            "scheduled_at": float(data.get("scheduled_at") or 0.0),
            "duration_min": int(data.get("duration_min") or 30),
            "location": str(data.get("location") or ""),
            "status": str(data.get("status") or "scheduled"),
            "completed": bool(data.get("completed")),
            "created_ts": float(data.get("created_at") or 0.0),
            "payload": dict(data),
        }
        return await self._upsert_row(_MEETINGS, "meeting_id", meeting_id, tenant_id, values, data)

    async def get_meeting(self, tenant_id: str, meeting_id: str) -> dict[str, Any] | None:
        return await self._fetch_one(
            select(_MEETINGS).where(_MEETINGS.c.meeting_id == meeting_id, _MEETINGS.c.tenant_id == tenant_id)
        )

    async def list_meetings(self, tenant_id: str) -> list[dict[str, Any]]:
        return await self._fetch_all(select(_MEETINGS).where(_MEETINGS.c.tenant_id == tenant_id))

    async def delete_meeting(self, tenant_id: str, meeting_id: str) -> bool:
        return await self._delete_row(_MEETINGS, "meeting_id", meeting_id, tenant_id)

    async def count_meetings(self, tenant_id: str) -> int:
        return await self._count_rows(_MEETINGS, tenant_id)

    async def upsert_reminder(self, tenant_id: str, data: dict[str, Any]) -> dict[str, Any]:
        reminder_id = str(data["reminder_id"])
        values = {
            "tenant_id": tenant_id,
            "task_id": str(data.get("task_id") or ""),
            "customer_id": str(data.get("customer_id") or ""),
            "lead_id": str(data.get("lead_id") or ""),
            "deal_id": str(data.get("deal_id") or ""),
            "title": str(data.get("title") or data.get("message") or ""),
            "message": str(data.get("message") or data.get("title") or ""),
            "assigned_agent_id": str(data.get("assigned_agent_id") or data.get("assigned_to") or ""),
            "trigger_at": float(data.get("trigger_at") or data.get("remind_at") or 0.0),
            "status": str(data.get("status") or "pending"),
            "triggered": bool(data.get("triggered")),
            "created_ts": float(data.get("created_at") or 0.0),
            "payload": dict(data),
        }
        return await self._upsert_row(_REMINDERS, "reminder_id", reminder_id, tenant_id, values, data)

    async def get_reminder(self, tenant_id: str, reminder_id: str) -> dict[str, Any] | None:
        return await self._fetch_one(
            select(_REMINDERS).where(_REMINDERS.c.reminder_id == reminder_id, _REMINDERS.c.tenant_id == tenant_id)
        )

    async def list_reminders(self, tenant_id: str) -> list[dict[str, Any]]:
        return await self._fetch_all(select(_REMINDERS).where(_REMINDERS.c.tenant_id == tenant_id))

    async def delete_reminder(self, tenant_id: str, reminder_id: str) -> bool:
        return await self._delete_row(_REMINDERS, "reminder_id", reminder_id, tenant_id)

    async def count_reminders(self, tenant_id: str) -> int:
        return await self._count_rows(_REMINDERS, tenant_id)
