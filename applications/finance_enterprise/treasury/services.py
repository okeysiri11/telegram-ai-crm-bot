"""Treasury dashboards and knowledge graph."""

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


class TreasuryKnowledge:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.bases = list(DEFAULT_CONFIG.tr_knowledge_bases)

    def publish(self, *, base: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if base not in self.bases:
            raise ValidationError(f"base must be one of {self.bases}")
        if not key:
            raise ValidationError("key required")
        eid = _id("tr_kg")
        return self.store.tr_knowledge.save(
            eid,
            {
                "entry_id": eid,
                "base": base,
                "key": key,
                "payload": payload or {},
                "graph_node": f"tr:{base}:{key}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"entries": self.store.tr_knowledge.count(), "bases": self.bases}


class TreasuryDashboard:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.types = list(DEFAULT_CONFIG.tr_dashboard_types)

    def render(self, *, dashboard_type: str = "treasury") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "treasury": {
                "pools": self.store.tr_pools.count(),
                "positions": self.store.tr_positions.count(),
                "operations": self.store.tr_operations.count(),
            },
            "budget": {
                "budgets": self.store.tr_budgets.count(),
                "approvals": self.store.tr_budget_approvals.count(),
                "revisions": self.store.tr_budget_revisions.count(),
            },
            "forecast": {
                "forecasts": self.store.tr_forecasts.count(),
                "scenarios": self.store.tr_scenarios.count(),
                "sensitivity": self.store.tr_sensitivity.count(),
            },
            "liquidity": {
                "liquidity": self.store.tr_liquidity.count(),
                "intercompany": self.store.tr_intercompany.count(),
            },
            "planning": {
                "workspaces": self.store.tr_workspaces.count(),
                "plans": self.store.tr_plans.count(),
                "variances": self.store.tr_variances.count(),
            },
        }[dashboard_type]
        did = _id("tr_dash")
        return self.store.tr_dashboards.save(
            did,
            {
                "dashboard_id": did,
                "dashboard_type": dashboard_type,
                "metrics": metrics,
                "generated_at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.tr_dashboards.count(), "types": self.types}
