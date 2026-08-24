# CRMEngine — unified CRM and sales pipeline facade.

from __future__ import annotations

from typing import Any

from applications.auto_marketplace.activities.service import ActivityService, activity_service
from applications.auto_marketplace.calendar.service import CalendarService, calendar_service
from applications.auto_marketplace.communications.service import CommunicationService, communication_service
from applications.auto_marketplace.crm.ai_assistant import AISalesAssistant, ai_sales_assistant
from applications.auto_marketplace.crm.security import CRMSecurity, crm_security
from applications.auto_marketplace.crm.workflow_bridge import CRMWorkflowBridge, crm_workflow_bridge
from applications.auto_marketplace.crm.automation import CRMAutomationEngine
from applications.auto_marketplace.crm.intelligence import CRMIntelligenceService
from applications.auto_marketplace.crm.execution import CRMExecutionEngine
from applications.auto_marketplace.crm.customer_360 import Customer360Service
from applications.auto_marketplace.crm.manager_intelligence import ManagerIntelligenceService
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
        self.automation = CRMAutomationEngine(
            leads=self.leads,
            deals=self.deals,
            tasks=self.tasks,
            calendar=self.calendar,
            activities=self.activities,
        )
        self.intelligence = CRMIntelligenceService(
            leads=self.leads,
            deals=self.deals,
            tasks=self.tasks,
            calendar=self.calendar,
            activities=self.activities,
            communications=self.communications,
            automation=self.automation,
            customers=self.customers,
        )
        self.execution = CRMExecutionEngine(
            intelligence=self.intelligence,
            automation=self.automation,
            leads=self.leads,
            deals=self.deals,
            tasks=self.tasks,
        )
        self.customer_360 = Customer360Service(
            customers=self.customers,
            leads=self.leads,
            deals=self.deals,
            activities=self.activities,
            communications=self.communications,
            tasks=self.tasks,
            calendar=self.calendar,
            automation=self.automation,
            execution=self.execution,
        )
        self.manager = ManagerIntelligenceService(
            deals=self.deals,
            leads=self.leads,
            tasks=self.tasks,
            activities=self.activities,
            automation=self.automation,
            execution=self.execution,
            intelligence=self.intelligence,
        )

    async def metrics(self) -> dict[str, Any]:
        from applications.auto_marketplace.crm.metrics import crm_metrics

        counts = await crm_metrics.refresh()
        return {
            "customers": counts["customers"],
            "leads": counts["leads"],
            "deals": counts["deals"],
            "tasks": counts["tasks"],
            "activities": counts["activities"],
            "calls": counts["calls"],
            "emails": counts["emails"],
            "meetings": counts["meetings"],
            "reminders": counts["reminders"],
            "opportunities": counts["opportunities"],
            "leads_by_status": counts["leads_by_status"],
            "deals_by_stage": counts["deals_by_stage"],
            "conversion": await self.pipeline.conversion_analytics(),
            "forecast": await self.pipeline.forecast(),
        }

    async def follow_up(self) -> dict[str, Any]:
        overdue = await self.tasks.list_tasks(overdue=True)
        due = await self.tasks.list_tasks(due=True)
        recent = await self.activities.list_activities()
        overdue_reminders = await self.calendar.list_reminders(overdue=True)
        upcoming_reminders = await self.calendar.list_reminders(upcoming=True)
        return {
            "overdue_tasks": [t.to_dict() for t in overdue],
            "due_tasks": [t.to_dict() for t in due],
            "recent_activities": [a.to_dict() for a in recent[:50]],
            "overdue_reminders": [r.to_dict() for r in overdue_reminders],
            "upcoming_reminders": [r.to_dict() for r in upcoming_reminders],
        }


crm_engine = CRMEngine()
