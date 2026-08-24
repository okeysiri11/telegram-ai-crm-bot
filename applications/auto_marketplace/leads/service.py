# LeadService — enterprise lead CRUD and qualification.

from __future__ import annotations

import time

from events.publisher import publish
from applications.auto_marketplace.crm.ai_assistant import AISalesAssistant, ai_sales_assistant
from applications.auto_marketplace.crm.events import LeadCreatedEvent, LeadQualifiedEvent
from applications.auto_marketplace.crm.models import CRMLead, CRMLeadStatus, CustomerProfile, LeadSource
from applications.auto_marketplace.crm.persistence import CRMPersistence, get_crm_persistence
from applications.auto_marketplace.crm.workflow_bridge import CRMWorkflowBridge, crm_workflow_bridge
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class LeadService:
    def __init__(
        self,
        store: MarketplaceStore | None = None,
        ai: AISalesAssistant | None = None,
        workflow: CRMWorkflowBridge | None = None,
        persistence: CRMPersistence | None = None,
    ) -> None:
        self._store = store or marketplace_store
        self._ai = ai or ai_sales_assistant
        self._workflow = workflow or crm_workflow_bridge
        self._persistence = persistence

    def _records(self) -> CRMPersistence:
        return self._persistence or get_crm_persistence()

    async def create(self, lead: CRMLead, customer: CustomerProfile | None = None) -> CRMLead:
        lead.score = await self._ai.score_lead(lead, customer)
        saved = await self._records().save_lead(lead)
        await publish(LeadCreatedEvent(lead_id=saved.lead_id, customer_id=saved.customer_id, source=saved.source.value))
        from applications.auto_marketplace.activities.service import activity_service

        await activity_service.record_event(
            "lead_created",
            subject="Lead created",
            body=saved.notes,
            customer_id=saved.customer_id,
            lead_id=saved.lead_id,
            agent_id=saved.assigned_agent_id,
            idempotency_key=f"lead_created:{saved.lead_id}",
        )
        wf_id = await self._workflow.assign_lead(saved.lead_id, dealer_id=saved.dealer_id)
        if wf_id:
            saved.metadata["assignment_workflow_id"] = wf_id
            saved = await self._records().save_lead(saved)
        return saved

    async def get(self, lead_id: str) -> CRMLead:
        lead = await self._records().get_lead(lead_id)
        if lead is None:
            raise NotFoundError("CRMLead", lead_id)
        return lead

    async def list_leads(
        self,
        *,
        status: CRMLeadStatus | None = None,
        dealer_id: str | None = None,
        customer_id: str | None = None,
    ) -> list[CRMLead]:
        items = await self._records().list_leads()
        if status:
            items = [lead for lead in items if lead.status == status]
        if dealer_id:
            items = [lead for lead in items if lead.dealer_id == dealer_id]
        if customer_id:
            items = [lead for lead in items if lead.customer_id == customer_id]
        return items

    async def qualify(self, lead_id: str, *, agent_id: str = "") -> CRMLead:
        lead = await self.get(lead_id)
        already = lead.status == CRMLeadStatus.QUALIFIED
        lead.status = CRMLeadStatus.QUALIFIED
        if lead.qualified_at is None:
            lead.qualified_at = time.time()
        lead.assigned_agent_id = agent_id or lead.assigned_agent_id
        lead.score = await self._ai.score_lead(lead)
        saved = await self._records().save_lead(lead)
        if not already:
            await publish(LeadQualifiedEvent(lead_id=lead_id, score=saved.score, agent_id=saved.assigned_agent_id))
            from applications.auto_marketplace.activities.service import activity_service

            await activity_service.record_event(
                "status_change",
                subject="Lead qualified",
                body="qualified",
                customer_id=saved.customer_id,
                lead_id=saved.lead_id,
                agent_id=saved.assigned_agent_id,
                idempotency_key=f"lead_status:{saved.lead_id}:qualified",
            )
        return saved

    async def set_status(self, lead_id: str, status: CRMLeadStatus) -> CRMLead:
        return await self.update(lead_id, status=status)

    async def assign(self, lead_id: str, agent_id: str) -> CRMLead:
        return await self.update(lead_id, assigned_agent_id=agent_id)

    @staticmethod
    def _coerce_update(key: str, value: object) -> object:
        if key == "status":
            if isinstance(value, CRMLeadStatus):
                return value
            try:
                return CRMLeadStatus(str(value))
            except ValueError as exc:
                raise ValidationError(f"invalid lead status: {value!r}") from exc
        if key == "source":
            if isinstance(value, LeadSource):
                return value
            try:
                return LeadSource(str(value))
            except ValueError as exc:
                raise ValidationError(f"invalid lead source: {value!r}") from exc
        return value

    async def update(self, lead_id: str, **updates: object) -> CRMLead:
        lead = await self.get(lead_id)
        previous_status = lead.status
        for key, value in updates.items():
            if hasattr(lead, key) and value is not None:
                setattr(lead, key, self._coerce_update(key, value))
        saved = await self._records().save_lead(lead)
        if "status" in updates and saved.status != previous_status:
            from applications.auto_marketplace.activities.service import activity_service

            await activity_service.record_event(
                "status_change",
                subject="Lead status changed",
                body=f"{previous_status.value}->{saved.status.value}",
                customer_id=saved.customer_id,
                lead_id=saved.lead_id,
                agent_id=saved.assigned_agent_id,
                idempotency_key=f"lead_status:{saved.lead_id}:{saved.status.value}",
            )
        return saved

    async def delete(self, lead_id: str) -> bool:
        await self.get(lead_id)
        return await self._records().delete_lead(lead_id)


lead_service = LeadService()
