"""Workflow templates — ready-made business process blueprints."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store
from applications.enterprise_hub.workflow.models import TEMPLATE_KINDS
from applications.enterprise_hub.workflow.workflow_manager import WorkflowManager


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


TEMPLATE_BLOCKS: dict[str, list[dict[str, Any]]] = {
    "crm_lead_processing": [
        {"type": "start"},
        {"type": "notification", "config": {"channel": "email", "target": "sales"}},
        {"type": "api_call", "config": {"url": "/crm/leads"}},
        {"type": "finish"},
    ],
    "invoice_approval": [
        {"type": "start"},
        {"type": "approval", "config": {"mode": "sequential", "approvers": ["cfo"]}},
        {"type": "notification", "config": {"channel": "telegram", "target": "finance"}},
        {"type": "finish"},
    ],
    "purchase_request": [
        {"type": "start"},
        {"type": "approval", "config": {"mode": "multi", "approvers": ["manager", "finance"]}},
        {"type": "finish"},
    ],
    "employee_onboarding": [
        {"type": "start"},
        {"type": "notification", "config": {"channel": "email", "target": "hr"}},
        {"type": "delay", "config": {"seconds": 0}},
        {"type": "finish"},
    ],
    "contract_approval": [
        {"type": "start"},
        {"type": "approval", "config": {"mode": "ai"}},
        {"type": "approval", "config": {"mode": "single", "approvers": ["counsel"]}},
        {"type": "finish"},
    ],
    "ai_task_processing": [
        {"type": "start"},
        {"type": "ai_decision", "config": {}},
        {"type": "notification", "config": {"channel": "push", "target": "ops"}},
        {"type": "finish"},
    ],
    "customer_support": [
        {"type": "start"},
        {"type": "decision", "config": {"condition_type": "status", "expected": "open"}},
        {"type": "notification", "config": {"channel": "email", "target": "support"}},
        {"type": "finish"},
    ],
    "equipment_maintenance": [
        {"type": "start"},
        {"type": "delay", "config": {"seconds": 0}},
        {"type": "api_call", "config": {"url": "/assets/maintain"}},
        {"type": "finish"},
    ],
}

TEMPLATE_TRIGGERS = {
    "crm_lead_processing": "lead_created",
    "invoice_approval": "payment_received",
    "purchase_request": "api",
    "employee_onboarding": "api",
    "contract_approval": "document_changed",
    "ai_task_processing": "ai_agent",
    "customer_support": "message_received",
    "equipment_maintenance": "schedule",
}


class WorkflowTemplates:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.manager = WorkflowManager(self.store)

    def instantiate(self, *, kind: str, name: str = "") -> dict[str, Any]:
        k = kind.lower().strip()
        if k not in TEMPLATE_KINDS:
            raise ValidationError(f"kind must be one of {list(TEMPLATE_KINDS)}")
        wf = self.manager.create(
            name=name or k.replace("_", " ").title(),
            trigger=TEMPLATE_TRIGGERS[k],
            blocks=TEMPLATE_BLOCKS[k],
            module="template",
        )
        self.manager.publish(workflow_id=wf["workflow_id"])
        tid = _id("wf_tpl")
        return self.store.wf_templates.save(
            tid,
            {
                "template_id": tid,
                "kind": k,
                "workflow_id": wf["workflow_id"],
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"templates": self.store.wf_templates.count(), "kinds": list(TEMPLATE_KINDS)}
