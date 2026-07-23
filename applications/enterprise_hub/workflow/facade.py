"""Workflow Suite facade — Sprint 19.5."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store
from applications.enterprise_hub.workflow.services import WorkflowDashboard, WorkflowOptimization
from applications.enterprise_hub.workflow.workflow_engine import WorkflowEngine
from applications.enterprise_hub.workflow.workflow_events import WorkflowEvents
from applications.enterprise_hub.workflow.workflow_executor import WorkflowExecutor
from applications.enterprise_hub.workflow.workflow_history import WorkflowHistory
from applications.enterprise_hub.workflow.workflow_manager import WorkflowManager
from applications.enterprise_hub.workflow.workflow_scheduler import WorkflowScheduler
from applications.enterprise_hub.workflow.workflow_templates import WorkflowTemplates
from applications.enterprise_hub.workflow.workflow_validator import WorkflowValidator


class WorkflowSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.manager = WorkflowManager(self.store)
        self.validator = WorkflowValidator(self.store)
        self.executor = WorkflowExecutor(self.store)
        self.engine = WorkflowEngine(
            self.store,
            manager=self.manager,
            validator=self.validator,
            executor=self.executor,
        )
        self.scheduler = WorkflowScheduler(self.store)
        self.history = WorkflowHistory(self.store)
        self.templates = WorkflowTemplates(self.store)
        self.events = WorkflowEvents(self.store)
        self.optimization = WorkflowOptimization(self.store)
        self.dashboard = WorkflowDashboard(self.store)

    def bootstrap(self) -> dict[str, Any]:
        lead = self.manager.create(
            name="CRM Lead Flow",
            trigger="lead_created",
            blocks=[
                {"type": "start"},
                {"type": "notification", "config": {"channel": "email", "target": "sales@bidex.io"}},
                {"type": "decision", "config": {"condition_type": "status", "expected": "open"}},
                {"type": "finish"},
            ],
            module="crm",
        )
        self.manager.add_block(
            workflow_id=lead["workflow_id"],
            block_type="api_call",
            config={"url": "/crm/enrich"},
        )
        self.manager.publish(workflow_id=lead["workflow_id"])
        ver = self.manager.version(workflow_id=lead["workflow_id"], note="bootstrap v2")
        val = self.validator.validate(workflow_id=lead["workflow_id"])

        invoice = self.templates.instantiate(kind="invoice_approval")
        purchase = self.templates.instantiate(kind="purchase_request")
        onboard = self.templates.instantiate(kind="employee_onboarding")
        contract = self.templates.instantiate(kind="contract_approval")
        ai_task = self.templates.instantiate(kind="ai_task_processing")
        support = self.templates.instantiate(kind="customer_support")
        maintain = self.templates.instantiate(kind="equipment_maintenance")
        crm_tpl = self.templates.instantiate(kind="crm_lead_processing")

        run_lead = self.engine.run(
            workflow_id=lead["workflow_id"],
            executor="system",
            context={"status": "open", "recipient": "sales@bidex.io"},
        )
        run_inv = self.engine.run(
            workflow_id=invoice["workflow_id"],
            executor="cfo",
            context={"status": "pending"},
        )
        adhoc = self.engine.run(
            trigger="webhook",
            name="Webhook Adhoc",
            executor="api",
            context={"status": "open"},
            blocks=[
                {"type": "start"},
                {"type": "approval", "config": {"mode": "auto"}},
                {"type": "finish"},
            ],
        )

        sched_cron = self.scheduler.schedule(
            workflow_id=maintain["workflow_id"],
            kind="cron",
            expression="0 6 * * 1",
        )
        sched_delay = self.scheduler.schedule(
            workflow_id=onboard["workflow_id"],
            kind="delayed",
            delay_seconds=60,
        )
        fire = self.scheduler.fire(schedule_id=sched_cron["schedule_id"])

        eng = self.store.wf_engine_runs.get(run_lead["engine_run_id"])
        hist = self.history.get(execution_id=eng["execution_id"])

        evt = self.events.emit(
            event_type="workflow.completed",
            workflow_id=lead["workflow_id"],
            payload={"result": "completed"},
        )
        opt = self.optimization.analyze(workflow_id=lead["workflow_id"])

        dash_p = self.dashboard.render(dashboard_type="performance")
        dash_a = self.dashboard.render(dashboard_type="approvals")
        dash_s = self.dashboard.render(dashboard_type="scheduler")
        dash_t = self.dashboard.render(dashboard_type="templates")
        dash_o = self.dashboard.render(dashboard_type="optimization")

        return {
            "bootstrap": True,
            "workflow_lead_id": lead["workflow_id"],
            "version_id": ver["version_id"],
            "validation_id": val["validation_id"],
            "template_invoice_id": invoice["template_id"],
            "template_purchase_id": purchase["template_id"],
            "template_onboarding_id": onboard["template_id"],
            "template_contract_id": contract["template_id"],
            "template_ai_task_id": ai_task["template_id"],
            "template_support_id": support["template_id"],
            "template_maintenance_id": maintain["template_id"],
            "template_crm_id": crm_tpl["template_id"],
            "engine_run_lead_id": run_lead["engine_run_id"],
            "engine_run_invoice_id": run_inv["engine_run_id"],
            "engine_run_adhoc_id": adhoc["engine_run_id"],
            "schedule_cron_id": sched_cron["schedule_id"],
            "schedule_delayed_id": sched_delay["schedule_id"],
            "fire_id": fire["fire_id"],
            "history_execution_id": hist["execution_id"],
            "event_id": evt["event_id"],
            "optimization_id": opt["optimization_id"],
            "dashboard_performance_id": dash_p["dashboard_id"],
            "dashboard_approvals_id": dash_a["dashboard_id"],
            "dashboard_scheduler_id": dash_s["dashboard_id"],
            "dashboard_templates_id": dash_t["dashboard_id"],
            "dashboard_optimization_id": dash_o["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "engine": self.engine.status(),
            "manager": self.manager.status(),
            "validator": self.validator.status(),
            "executor": self.executor.status(),
            "scheduler": self.scheduler.status(),
            "history": self.history.status(),
            "templates": self.templates.status(),
            "events": self.events.status(),
            "optimization": self.optimization.status(),
            "dashboard": self.dashboard.status(),
        }


workflow = WorkflowSuite()
