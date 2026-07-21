# CRMEngine — farmer/buyer/supplier/exporter CRM, leads, tasks, timeline.

from __future__ import annotations

import time
from typing import Any

from events.publisher import publish

from applications.agro_marketplace.marketplace.ai_integration import TradingAIIntegration, trading_ai
from applications.agro_marketplace.marketplace.events import BuyerRegisteredEvent, FarmerRegisteredTradingEvent
from applications.agro_marketplace.marketplace.models import (
    AgriculturalLead,
    BuyerProfile,
    CRMContactEntry,
    CRMTask,
    ExporterProfile,
    FarmerProfile,
    LeadStatus,
    SupplierProfile,
)
from applications.agro_marketplace.marketplace.workflow import TradingWorkflowBridge, trading_workflow
from applications.agro_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.agro_marketplace.shared.models import Buyer, Farmer, Supplier
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class CRMEngine:
    def __init__(
        self,
        store: AgroStore | None = None,
        ai: TradingAIIntegration | None = None,
        workflow: TradingWorkflowBridge | None = None,
    ) -> None:
        self._store = store or agro_store
        self._ai = ai or trading_ai
        self._workflow = workflow or trading_workflow

    # --- Profiles ---

    async def register_farmer(self, profile: FarmerProfile) -> FarmerProfile:
        if not profile.name or not profile.email:
            raise ValidationError("name and email are required")
        if not profile.farmer_id:
            profile.farmer_id = profile.profile_id
        legacy = Farmer(
            farmer_id=profile.farmer_id,
            name=profile.name,
            email=profile.email,
            phone=profile.phone,
            country=profile.country,
            region=profile.region,
            certifications=list(profile.certifications),
        )
        self._store.farmers.save(legacy.farmer_id, legacy)
        profile.updated_at = time.time()
        saved = self._store.farmer_profiles.save(profile.profile_id, profile)
        await publish(
            FarmerRegisteredTradingEvent(
                farmer_id=saved.farmer_id,
                profile_id=saved.profile_id,
                email=saved.email,
                name=saved.name,
            )
        )
        self._workflow.notify(saved.farmer_id, "Farmer registered", saved.name)
        return saved

    def list_farmer_profiles(self) -> list[FarmerProfile]:
        return self._store.farmer_profiles.list_all()

    def get_farmer_profile(self, profile_id: str) -> FarmerProfile:
        profile = self._store.farmer_profiles.get(profile_id)
        if profile is None:
            raise NotFoundError("FarmerProfile", profile_id)
        return profile

    async def register_buyer(self, profile: BuyerProfile) -> BuyerProfile:
        if not profile.name or not profile.email:
            raise ValidationError("name and email are required")
        if not profile.buyer_id:
            profile.buyer_id = profile.profile_id
        legacy = Buyer(
            buyer_id=profile.buyer_id,
            name=profile.name,
            email=profile.email,
            buyer_type=profile.buyer_type,
            country=profile.country,
        )
        self._store.buyers.save(legacy.buyer_id, legacy)
        profile.updated_at = time.time()
        saved = self._store.buyer_profiles.save(profile.profile_id, profile)
        await publish(
            BuyerRegisteredEvent(
                buyer_id=saved.buyer_id,
                profile_id=saved.profile_id,
                email=saved.email,
                name=saved.name,
            )
        )
        self._workflow.notify(saved.buyer_id, "Buyer registered", saved.name)
        return saved

    def list_buyer_profiles(self) -> list[BuyerProfile]:
        return self._store.buyer_profiles.list_all()

    def get_buyer_profile(self, profile_id: str) -> BuyerProfile:
        profile = self._store.buyer_profiles.get(profile_id)
        if profile is None:
            raise NotFoundError("BuyerProfile", profile_id)
        return profile

    def register_supplier(self, profile: SupplierProfile) -> SupplierProfile:
        if not profile.name:
            raise ValidationError("name is required")
        if not profile.supplier_id:
            profile.supplier_id = profile.profile_id
        legacy = Supplier(
            supplier_id=profile.supplier_id,
            name=profile.name,
            email=profile.email,
            category=profile.category,
            country=profile.country,
        )
        self._store.suppliers.save(legacy.supplier_id, legacy)
        profile.updated_at = time.time()
        return self._store.supplier_profiles.save(profile.profile_id, profile)

    def list_supplier_profiles(self) -> list[SupplierProfile]:
        return self._store.supplier_profiles.list_all()

    def register_exporter(self, profile: ExporterProfile) -> ExporterProfile:
        if not profile.name:
            raise ValidationError("name is required")
        if not profile.exporter_id:
            profile.exporter_id = profile.profile_id
        self._store.exporters.save(profile.exporter_id, profile)
        profile.updated_at = time.time()
        return self._store.exporter_profiles.save(profile.profile_id, profile)

    def list_exporter_profiles(self) -> list[ExporterProfile]:
        return self._store.exporter_profiles.list_all()

    # --- Leads ---

    async def create_lead(self, lead: AgriculturalLead) -> AgriculturalLead:
        lead.score = self._ai.score_lead(lead)
        lead.updated_at = time.time()
        saved = self._store.agro_leads.save(lead.lead_id, lead)
        # Keep legacy crm_leads in sync for foundation CRMService
        from applications.agro_marketplace.crm.service import AgroLead

        self._store.crm_leads.save(
            saved.lead_id,
            AgroLead(
                lead_id=saved.lead_id,
                name=saved.name,
                email=saved.email,
                role=saved.role,
                source=saved.source,
                status=saved.status.value,
                notes=saved.notes,
            ),
        )
        return saved

    def list_leads(self, *, status: LeadStatus | None = None) -> list[AgriculturalLead]:
        items = self._store.agro_leads.list_all()
        if status:
            items = [lead for lead in items if lead.status == status]
        return items

    def get_lead(self, lead_id: str) -> AgriculturalLead:
        lead = self._store.agro_leads.get(lead_id)
        if lead is None:
            raise NotFoundError("AgriculturalLead", lead_id)
        return lead

    async def assign_lead(self, lead_id: str, assignee_id: str) -> AgriculturalLead:
        lead = self.get_lead(lead_id)
        lead.assignee_id = assignee_id
        lead.status = LeadStatus.ASSIGNED
        lead.updated_at = time.time()
        saved = self._store.agro_leads.save(lead_id, lead)
        await self._workflow.start_lead_assignment(lead_id, assignee_id)
        self._workflow.notify(assignee_id, "Lead assigned", f"Lead {lead.name}")
        return saved

    def qualify_lead(self, lead_id: str) -> AgriculturalLead:
        lead = self.get_lead(lead_id)
        lead.status = LeadStatus.QUALIFIED
        lead.score = max(lead.score, self._ai.score_lead(lead))
        lead.updated_at = time.time()
        return self._store.agro_leads.save(lead_id, lead)

    # --- Timeline / tasks ---

    def add_contact(self, entry: CRMContactEntry) -> CRMContactEntry:
        return self._store.crm_contacts.save(entry.entry_id, entry)

    def timeline(self, profile_id: str) -> list[CRMContactEntry]:
        items = [c for c in self._store.crm_contacts.list_all() if c.profile_id == profile_id]
        return sorted(items, key=lambda c: c.created_at)

    def create_task(self, task: CRMTask) -> CRMTask:
        return self._store.crm_tasks.save(task.task_id, task)

    def list_tasks(self, *, assignee_id: str | None = None) -> list[CRMTask]:
        items = self._store.crm_tasks.list_all()
        if assignee_id:
            items = [t for t in items if t.assignee_id == assignee_id]
        return items

    def complete_task(self, task_id: str) -> CRMTask:
        task = self._store.crm_tasks.get(task_id)
        if task is None:
            raise NotFoundError("CRMTask", task_id)
        task.status = "done"
        return self._store.crm_tasks.save(task_id, task)

    def metrics(self) -> dict[str, Any]:
        return {
            "farmer_profiles": self._store.farmer_profiles.count(),
            "buyer_profiles": self._store.buyer_profiles.count(),
            "supplier_profiles": self._store.supplier_profiles.count(),
            "exporter_profiles": self._store.exporter_profiles.count(),
            "leads": self._store.agro_leads.count(),
            "tasks": self._store.crm_tasks.count(),
            "contacts": self._store.crm_contacts.count(),
        }


crm_engine = CRMEngine()
