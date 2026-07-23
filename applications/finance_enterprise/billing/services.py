"""Billing dashboards and knowledge graph."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.finance_enterprise.config import DEFAULT_CONFIG
from applications.finance_enterprise.shared.exceptions import ValidationError
from applications.finance_enterprise.shared.store import FinanceEnterpriseStore, finance_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class BillingKnowledge:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.bases = list(DEFAULT_CONFIG.bil_knowledge_bases)

    def publish(self, *, base: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if base not in self.bases:
            raise ValidationError(f"base must be one of {self.bases}")
        if not key:
            raise ValidationError("key required")
        eid = _id("bil_kg")
        return self.store.bil_knowledge.save(
            eid,
            {
                "entry_id": eid,
                "base": base,
                "key": key,
                "payload": payload or {},
                "graph_node": f"bil:{base}:{key}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"entries": self.store.bil_knowledge.count(), "bases": self.bases}


class BillingDashboard:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.types = list(DEFAULT_CONFIG.bil_dashboard_types)

    def render(self, *, dashboard_type: str = "invoice") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "invoice": {
                "invoices": self.store.bil_invoices.count(),
                "quotations": self.store.bil_quotations.count(),
                "credit_notes": self.store.bil_credit_notes.count(),
            },
            "receivables": {
                "receivables": self.store.bil_receivables.count(),
                "collections": self.store.bil_collections.count(),
                "aging": self.store.bil_aging.count(),
            },
            "payables": {
                "bills": self.store.bil_bills.count(),
                "schedules": self.store.bil_ap_schedules.count(),
                "approvals": self.store.bil_ap_approvals.count(),
            },
            "tax": {
                "taxes": self.store.bil_taxes.count(),
                "calculations": self.store.bil_tax_calcs.count(),
                "reports": self.store.bil_tax_reports.count(),
            },
            "cashflow": {
                "receipts": self.store.bil_expected_receipts.count(),
                "payments": self.store.bil_expected_payments.count(),
                "forecasts": self.store.bil_forecasts.count(),
            },
        }[dashboard_type]
        did = _id("bil_dash")
        return self.store.bil_dashboards.save(
            did,
            {
                "dashboard_id": did,
                "dashboard_type": dashboard_type,
                "metrics": metrics,
                "generated_at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.bil_dashboards.count(), "types": self.types}
