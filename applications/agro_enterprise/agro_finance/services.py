"""Dashboards and knowledge for agro finance."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.agro_enterprise.shared.exceptions import ValidationError
from applications.agro_enterprise.shared.store import AgroEnterpriseStore, agro_enterprise_store

DASHBOARD_TYPES = ["finance", "commodity_exchange", "risk", "insurance", "market_intelligence"]
REGISTRY_TYPES = ["financial", "commodity", "contract", "insurance", "risk"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AgroFinanceDashboard:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store
        self.types = list(DASHBOARD_TYPES)

    def render(self, *, dashboard_type: str = "finance") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "finance": {
                "budgets": self.store.af_budgets.count(),
                "loans": self.store.af_loans.count(),
                "grants": self.store.af_grants.count(),
            },
            "commodity_exchange": {
                "commodities": self.store.af_commodities.count(),
                "orders": self.store.af_orders.count(),
                "trades": self.store.af_trades.count(),
            },
            "risk": {
                "risks": self.store.af_risks.count(),
                "warnings": self.store.af_warnings.count(),
            },
            "insurance": {
                "policies": self.store.af_policies.count(),
                "claims": self.store.af_claims.count(),
            },
            "market_intelligence": {
                "prices": self.store.af_prices.count(),
                "forecasts": self.store.af_forecasts.count(),
                "insights": self.store.af_insights.count(),
            },
        }[dashboard_type]
        did = _id("af_dash")
        return self.store.af_dashboards.save(
            did,
            {"dashboard_id": did, "dashboard_type": dashboard_type, "metrics": metrics, "generated_at": _now()},
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.af_dashboards.count(), "types": self.types}


class AgroFinanceKnowledge:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store
        self.types = list(REGISTRY_TYPES)

    def publish(self, *, registry_type: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if registry_type not in self.types:
            raise ValidationError(f"registry_type must be one of {self.types}")
        if not key:
            raise ValidationError("key required")
        rid = _id("af_reg")
        return self.store.af_registries.save(
            rid,
            {
                "registry_id": rid,
                "registry_type": registry_type,
                "key": key,
                "payload": payload or {},
                "graph_node": f"af:{registry_type}:{key}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"entries": self.store.af_registries.count(), "types": self.types}
