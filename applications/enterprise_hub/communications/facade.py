"""Communications Suite facade — Sprint 19.4."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.communications.audit import CommunicationsAudit
from applications.enterprise_hub.communications.channels.corporate_chat import CorporateChat
from applications.enterprise_hub.communications.delivery import DeliveryEngine
from applications.enterprise_hub.communications.notification_center import NotificationCenter
from applications.enterprise_hub.communications.notification_router import NotificationRouter
from applications.enterprise_hub.communications.priority import PriorityEngine
from applications.enterprise_hub.communications.queue import NotificationQueue
from applications.enterprise_hub.communications.services import CommunicationsDashboard
from applications.enterprise_hub.communications.templates.engine import TemplateEngine
from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class CommunicationsSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.center = NotificationCenter(self.store)
        self.priority = PriorityEngine(self.store)
        self.queue = NotificationQueue(self.store)
        self.delivery = DeliveryEngine(self.store)
        self.router = NotificationRouter(
            self.store,
            priority=self.priority,
            queue=self.queue,
            delivery=self.delivery,
        )
        self.templates = TemplateEngine(self.store)
        self.chat = CorporateChat(self.store)
        self.audit = CommunicationsAudit(self.store)
        self.dashboard = CommunicationsDashboard(self.store)

    def bootstrap(self) -> dict[str, Any]:
        evt_lead = self.center.publish(
            source="crm",
            event="new_lead",
            recipient="sales@bidex.io",
            subject="New Lead Acme",
            body="Lead created",
            template="lead",
            payload={"company": "Acme"},
        )
        evt_crit = self.center.publish(
            source="platform",
            event="server_down",
            recipient="ops@bidex.io",
            subject="Server Down",
            body="Primary API unreachable",
            payload={"severity": "critical"},
        )
        evt_inv = self.center.publish(
            source="finance",
            event="invoice_ready",
            recipient="cfo@bidex.io",
            subject="Invoice INV-9001",
            body="Invoice ready for review",
            channel="email",
            priority="high",
            template="invoice",
        )

        prio = self.priority.classify(subject="Server Down", event="server_down")
        route_crit = self.router.route(event_id=evt_crit["event_id"], fallback=True)
        route_lead = self.router.route(event_id=evt_lead["event_id"], fallback=True)
        route_inv = self.router.route(event_id=evt_inv["event_id"], fallback=False)
        smart = self.router.smart_route(
            source="legal",
            event="approval_required",
            recipient="counsel@bidex.io",
            subject="Contract Approval",
            body="CTR-2026-01 awaiting sign-off",
        )

        tpl_crm = self.templates.register(kind="crm", name="CRM Default", fmt="markdown")
        tpl_inv = self.templates.register(kind="invoice", name="Invoice Default", fmt="html")
        tpl_lead = self.templates.register(kind="lead", name="Lead Default", fmt="plain")
        tpl_task = self.templates.register(kind="task", name="Task Default")
        tpl_appr = self.templates.register(kind="approval", name="Approval Default")
        tpl_sec = self.templates.register(kind="security", name="Security Default")
        tpl_ai = self.templates.register(kind="ai_alert", name="AI Alert Default")
        tpl_rep = self.templates.register(kind="report", name="Report Default")

        rend = self.templates.render(
            template_id=tpl_lead["template_id"],
            variables={
                "name": "Alex",
                "project": "Hub",
                "date": "2026-07-23",
                "company": "Bidex",
                "status": "new",
            },
            fmt="plain",
        )

        batch = self.queue.dequeue_batch(limit=5)
        deliv_ids = route_crit.get("delivery_ids") or []
        read = None
        retry = None
        if deliv_ids:
            read = self.delivery.mark_read(delivery_id=deliv_ids[0])
            retry = self.delivery.retry(delivery_id=deliv_ids[-1], error="transient")

        chat_emp = self.chat.send(
            from_party="cfo@bidex.io",
            to_party="ops@bidex.io",
            message="Confirm outage window",
            party_type="employee",
        )
        chat_ai = self.chat.ai_to_ai(
            from_agent="finance_agent",
            to_agent="legal_agent",
            message="Need contract status for INV-9001",
        )
        chat_svc = self.chat.service_bus(
            from_service="crm",
            to_service="enterprise_hub",
            message="lead.created",
        )

        aud = self.audit.record(
            sender="platform",
            recipient="ops@bidex.io",
            route_id=route_crit["route_id"],
            template="",
            status="delivered",
            delivery_confirmed=True,
            read_confirmed=bool(read),
            retries=1 if retry else 0,
            detail="Sprint 19.4 bootstrap",
        )

        dash_d = self.dashboard.render(dashboard_type="delivery")
        dash_q = self.dashboard.render(dashboard_type="queue")
        dash_c = self.dashboard.render(dashboard_type="channels")
        dash_a = self.dashboard.render(dashboard_type="audit")
        dash_an = self.dashboard.render(dashboard_type="analytics")

        return {
            "bootstrap": True,
            "event_lead_id": evt_lead["event_id"],
            "event_critical_id": evt_crit["event_id"],
            "event_invoice_id": evt_inv["event_id"],
            "priority_id": prio["priority_id"],
            "route_critical_id": route_crit["route_id"],
            "route_lead_id": route_lead["route_id"],
            "route_invoice_id": route_inv["route_id"],
            "smart_route_id": smart["route_id"],
            "template_crm_id": tpl_crm["template_id"],
            "template_invoice_id": tpl_inv["template_id"],
            "template_lead_id": tpl_lead["template_id"],
            "template_task_id": tpl_task["template_id"],
            "template_approval_id": tpl_appr["template_id"],
            "template_security_id": tpl_sec["template_id"],
            "template_ai_alert_id": tpl_ai["template_id"],
            "template_report_id": tpl_rep["template_id"],
            "render_id": rend["render_id"],
            "batch_size": len(batch),
            "read_delivery_id": read["delivery_id"] if read else "",
            "retry_id": retry["retry_id"] if retry else "",
            "chat_employee_id": chat_emp["chat_id"],
            "chat_ai_id": chat_ai["chat_id"],
            "chat_service_id": chat_svc["chat_id"],
            "audit_id": aud["audit_id"],
            "dashboard_delivery_id": dash_d["dashboard_id"],
            "dashboard_queue_id": dash_q["dashboard_id"],
            "dashboard_channels_id": dash_c["dashboard_id"],
            "dashboard_audit_id": dash_a["dashboard_id"],
            "dashboard_analytics_id": dash_an["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "center": self.center.status(),
            "priority": self.priority.status(),
            "queue": self.queue.status(),
            "delivery": self.delivery.status(),
            "router": self.router.status(),
            "templates": self.templates.status(),
            "chat": self.chat.status(),
            "audit": self.audit.status(),
            "dashboard": self.dashboard.status(),
        }


communications = CommunicationsSuite()
