# CRMEngine — unified CRM and sales pipeline facade.

from __future__ import annotations

from typing import Any

from applications.auto_marketplace.activities.service import ActivityService, activity_service
from applications.auto_marketplace.calendar.service import CalendarService, calendar_service
from applications.auto_marketplace.communications.service import CommunicationService, communication_service
from applications.auto_marketplace.crm.ai_assistant import AISalesAssistant, ai_sales_assistant
from applications.auto_marketplace.crm.security import CRMSecurity, crm_security
from applications.auto_marketplace.crm.workflow_bridge import CRMWorkflowBridge, crm_workflow_bridge
from applications.auto_marketplace.customers.profile_service import CustomerProfileService, customer_profile_service
from applications.auto_marketplace.deals.service import DealService, deal_service
from applications.auto_marketplace.leads.service import LeadService, lead_service
from applications.auto_marketplace.sales_pipeline.service import SalesPipelineEngine, sales_pipeline_engine
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store
from applications.auto_marketplace.tasks.service import TaskService, task_service


class CRMEngine:
    """Enterprise CRM & Sales Pipeline entry point."""

    def __init__(
        self,
        store: MarketplaceStore | None = None,
        customers: CustomerProfileService | None = None,
        leads: LeadService | None = None,
        deals: DealService | None = None,
        pipeline: SalesPipelineEngine | None = None,
        activities: ActivityService | None = None,
        communications: CommunicationService | None = None,
        tasks: TaskService | None = None,
        calendar: CalendarService | None = None,
        ai: AISalesAssistant | None = None,
        security: CRMSecurity | None = None,
        workflow: CRMWorkflowBridge | None = None,
    ) -> None:
        self._store = store or marketplace_store
        self.customers = customers or customer_profile_service
        self.leads = leads or lead_service
        self.deals = deals or deal_service
        self.pipeline = pipeline or sales_pipeline_engine
        self.activities = activities or activity_service
        self.communications = communications or communication_service
        self.tasks = tasks or task_service
        self.calendar = calendar or calendar_service
        self.ai = ai or ai_sales_assistant
        self.security = security or crm_security
        self.workflow = workflow or crm_workflow_bridge

    def metrics(self) -> dict[str, Any]:
        return {
            "customers": self._store.customer_profiles.count(),
            "leads": self._store.crm_leads.count(),
            "deals": self._store.crm_deals.count(),
            "tasks": self._store.crm_tasks.count(),
            "conversion": self.pipeline.conversion_analytics(),
            "forecast": self.pipeline.forecast(),
        }


crm_engine = CRMEngine()
