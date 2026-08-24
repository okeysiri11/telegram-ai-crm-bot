# CommunicationService — phone calls and emails (durable via CRM persistence).

from __future__ import annotations

import time

from applications.auto_marketplace.activities.service import ActivityService, activity_service
from applications.auto_marketplace.crm.ai_assistant import AISalesAssistant, ai_sales_assistant
from applications.auto_marketplace.crm.models import EmailMessage, Interaction, InteractionType, PhoneCall
from applications.auto_marketplace.crm.persistence import CRMPersistence, get_crm_persistence
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store

_CALL_STATUSES = frozenset({"logged", "completed", "missed", "cancelled"})
_EMAIL_STATUSES = frozenset({"logged", "sent", "failed", "draft"})


class CommunicationService:
    def __init__(
        self,
        store: MarketplaceStore | None = None,
        activities: ActivityService | None = None,
        ai: AISalesAssistant | None = None,
        persistence: CRMPersistence | None = None,
    ) -> None:
        self._store = store or marketplace_store
        self._activities = activities or activity_service
        self._ai = ai or ai_sales_assistant
        self._persistence = persistence

    def _records(self) -> CRMPersistence:
        return self._persistence or get_crm_persistence()

    async def _assert_relations(self, customer_id: str, lead_id: str, deal_id: str) -> None:
        records = self._records()
        if customer_id and await records.get_customer(customer_id) is None:
            raise NotFoundError("CustomerProfile", customer_id)
        if lead_id and await records.get_lead(lead_id) is None:
            raise NotFoundError("CRMLead", lead_id)
        if deal_id and await records.get_deal(deal_id) is None:
            raise NotFoundError("CRMDeal", deal_id)

    async def log_call(self, call: PhoneCall) -> PhoneCall:
        await self._assert_relations(call.customer_id, call.lead_id, call.deal_id)
        now = time.time()
        call.updated_at = now
        if call.started_at is None:
            call.started_at = call.created_at or now
        if call.ended_at is None and call.duration_sec:
            call.ended_at = (call.started_at or now) + float(call.duration_sec)
        call.notes = call.notes or call.summary
        history: list = []
        if call.customer_id:
            history = await self._activities.list_activities(customer_id=call.customer_id)
        call.summary = await self._ai.summarize_conversation([i.to_dict() for i in history]) or call.summary
        saved = await self._records().save_call(call)
        await self._activities.log_interaction(
            Interaction(
                customer_id=saved.customer_id,
                lead_id=saved.lead_id,
                deal_id=saved.deal_id,
                interaction_type=InteractionType.CALL,
                subject=f"Phone call ({saved.direction})",
                body=saved.summary or saved.notes,
                agent_id=saved.agent_id,
                idempotency_key=f"call:{saved.call_id}",
            )
        )
        return saved

    async def get_call(self, call_id: str) -> PhoneCall:
        item = await self._records().get_call(call_id)
        if item is None:
            raise NotFoundError("PhoneCall", call_id)
        return item

    async def list_calls(
        self,
        *,
        customer_id: str | None = None,
        lead_id: str | None = None,
        deal_id: str | None = None,
        agent_id: str | None = None,
        status: str | None = None,
    ) -> list[PhoneCall]:
        items = await self._records().list_calls()
        if customer_id:
            items = [c for c in items if c.customer_id == customer_id]
        if lead_id:
            items = [c for c in items if c.lead_id == lead_id]
        if deal_id:
            items = [c for c in items if c.deal_id == deal_id]
        if agent_id:
            items = [c for c in items if c.agent_id == agent_id]
        if status:
            items = [c for c in items if c.status == status]
        return sorted(items, key=lambda c: c.created_at, reverse=True)

    async def update_call(self, call_id: str, **updates: object) -> PhoneCall:
        call = await self.get_call(call_id)
        for key, value in updates.items():
            if key == "notes":
                call.notes = str(value or "")
                call.summary = call.notes or call.summary
                continue
            if not hasattr(call, key) or value is None:
                continue
            if key == "status" and str(value) not in _CALL_STATUSES:
                raise ValidationError(f"invalid call status: {value!r}")
            setattr(call, key, value)
        await self._assert_relations(call.customer_id, call.lead_id, call.deal_id)
        call.updated_at = time.time()
        return await self._records().save_call(call)

    async def delete_call(self, call_id: str) -> bool:
        await self.get_call(call_id)
        return await self._records().delete_call(call_id)

    async def log_email(self, email: EmailMessage) -> EmailMessage:
        await self._assert_relations(email.customer_id, email.lead_id, email.deal_id)
        email.updated_at = time.time()
        saved = await self._records().save_email(email)
        await self._activities.log_interaction(
            Interaction(
                customer_id=saved.customer_id,
                lead_id=saved.lead_id,
                deal_id=saved.deal_id,
                interaction_type=InteractionType.EMAIL,
                subject=saved.subject,
                body=saved.body,
                agent_id=saved.agent_id,
                idempotency_key=f"email:{saved.email_id}",
            )
        )
        return saved

    async def get_email(self, email_id: str) -> EmailMessage:
        item = await self._records().get_email(email_id)
        if item is None:
            raise NotFoundError("EmailMessage", email_id)
        return item

    async def list_emails(
        self,
        *,
        customer_id: str | None = None,
        lead_id: str | None = None,
        deal_id: str | None = None,
        status: str | None = None,
    ) -> list[EmailMessage]:
        items = await self._records().list_emails()
        if customer_id:
            items = [e for e in items if e.customer_id == customer_id]
        if lead_id:
            items = [e for e in items if e.lead_id == lead_id]
        if deal_id:
            items = [e for e in items if e.deal_id == deal_id]
        if status:
            items = [e for e in items if e.status == status]
        return sorted(items, key=lambda e: e.created_at, reverse=True)

    async def update_email(self, email_id: str, **updates: object) -> EmailMessage:
        email = await self.get_email(email_id)
        for key, value in updates.items():
            if not hasattr(email, key) or value is None:
                continue
            if key == "status" and str(value) not in _EMAIL_STATUSES:
                raise ValidationError(f"invalid email status: {value!r}")
            setattr(email, key, value)
        await self._assert_relations(email.customer_id, email.lead_id, email.deal_id)
        email.updated_at = time.time()
        return await self._records().save_email(email)

    async def delete_email(self, email_id: str) -> bool:
        await self.get_email(email_id)
        return await self._records().delete_email(email_id)


communication_service = CommunicationService()
