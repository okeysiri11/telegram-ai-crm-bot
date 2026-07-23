"""Payments dashboards and knowledge graph."""

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


class PaymentsKnowledge:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.bases = list(DEFAULT_CONFIG.pay_knowledge_bases)

    def publish(self, *, base: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if base not in self.bases:
            raise ValidationError(f"base must be one of {self.bases}")
        if not key:
            raise ValidationError("key required")
        eid = _id("pay_kg")
        return self.store.pay_knowledge.save(
            eid,
            {
                "entry_id": eid,
                "base": base,
                "key": key,
                "payload": payload or {},
                "graph_node": f"pay:{base}:{key}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"entries": self.store.pay_knowledge.count(), "bases": self.bases}


class PaymentsDashboard:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.types = list(DEFAULT_CONFIG.pay_dashboard_types)

    def render(self, *, dashboard_type: str = "payments") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "payments": {
                "payments": self.store.pay_payments.count(),
                "approvals": self.store.pay_approvals.count(),
                "bulk": self.store.pay_bulk.count(),
            },
            "wallets": {
                "wallets": self.store.pay_wallets.count(),
                "history": self.store.pay_wallet_history.count(),
            },
            "banking": {
                "banks": self.store.pay_banks.count(),
                "accounts": self.store.pay_bank_accounts.count(),
                "statements": self.store.pay_statements.count(),
            },
            "cash": {
                "registers": self.store.pay_cash_registers.count(),
                "operations": self.store.pay_cash_ops.count(),
                "flows": self.store.pay_cash_flows.count(),
            },
        }[dashboard_type]
        did = _id("pay_dash")
        return self.store.pay_dashboards.save(
            did,
            {
                "dashboard_id": did,
                "dashboard_type": dashboard_type,
                "metrics": metrics,
                "generated_at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.pay_dashboards.count(), "types": self.types}
