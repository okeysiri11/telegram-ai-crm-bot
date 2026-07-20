# LeadService — enterprise lead CRUD and qualification.

from __future__ import annotations

import time

from events.publisher import publish
from applications.auto_marketplace.crm.ai_assistant import AISalesAssistant, ai_sales_assistant
from applications.auto_marketplace.crm.events import LeadCreatedEvent, LeadQualifiedEvent
from applications.auto_marketplace.crm.models import CRMLead, CRMLeadStatus, CustomerProfile
from applications.auto_marketplace.crm.workflow_bridge import CRMWorkflowBridge, crm_workflow_bridge
from applications.auto_marketplace.shared.exceptions import NotFoundError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class LeadService:
    def __init__(
        self,
        store: MarketplaceStore | None = None,
        ai: AISalesAssistant | None = None,
        workflow: CRMWorkflowBridge | None = None,
    ) -> None:
        self._store = store or marketplace_store
        self._ai = ai or ai_sales_assistant
        self._workflow = workflow or crm_workflow_bridge

    async def create(self, lead: CRMLead, customer: CustomerProfile | None = None) -> CRMLead:
        lead.score = await self._ai.score_lead(lead, customer)
        saved = self._store.crm_leads.save(lead.lead_id, lead)
        await publish(LeadCreatedEvent(lead_id=saved.lead_id, customer_id=saved.customer_id, source=saved.source.value))
        wf_id = await self._workflow.assign_lead(saved.lead_id, dealer_id=saved.dealer_id)
        if wf_id:
            saved.metadata["assignment_workflow_id"] = wf_id
            self._store.crm_leads.save(saved.lead_id, saved)
        return saved

    def get(self, lead_id: str) -> CRMLead:
        lead = self._store.crm_leads.get(lead_id)
        if lead is None:
            raise NotFoundError("CRMLead", lead_id)
        return lead

    def list_leads(self, *, status: CRMLeadStatus | None = None, dealer_id: str | None = None) -> list[CRMLead]:
        items = self._store.crm_leads.list_all()
        if status:
            items = [l for l in items if l.status == status]
        if dealer_id:
            items = [l for l in items if l.dealer_id == dealer_id]
        return items

    async def qualify(self, lead_id: str, *, agent_id: str = "") -> CRMLead:
        lead = self.get(lead_id)
        lead.status = CRMLeadStatus.QUALIFIED
        lead.qualified_at = time.time()
        lead.assigned_agent_id = agent_id or lead.assigned_agent_id
        lead.score = await self._ai.score_lead(lead)
        saved = self._store.crm_leads.save(lead_id, lead)
        await publish(LeadQualifiedEvent(lead_id=lead_id, score=saved.score, agent_id=saved.assigned_agent_id))
        return saved

    async def update(self, lead_id: str, **updates: object) -> CRMLead:
        lead = self.get(lead_id)
        for key, value in updates.items():
            if hasattr(lead, key) and value is not None:
                setattr(lead, key, value)
        return self._store.crm_leads.save(lead_id, lead)


lead_service = LeadService()
