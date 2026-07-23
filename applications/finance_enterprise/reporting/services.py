"""Reporting dashboards and knowledge graph."""

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


class ReportingKnowledge:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.bases = list(DEFAULT_CONFIG.rpt_knowledge_bases)

    def publish(self, *, base: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if base not in self.bases:
            raise ValidationError(f"base must be one of {self.bases}")
        if not key:
            raise ValidationError("key required")
        eid = _id("rpt_kg")
        return self.store.rpt_knowledge.save(
            eid,
            {
                "entry_id": eid,
                "base": base,
                "key": key,
                "payload": payload or {},
                "graph_node": f"rpt:{base}:{key}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"entries": self.store.rpt_knowledge.count(), "bases": self.bases}


class ReportingDashboard:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.types = list(DEFAULT_CONFIG.rpt_dashboard_types)

    def render(self, *, dashboard_type: str = "executive") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "executive": {
                "statements": self.store.rpt_statements.count(),
                "management": self.store.rpt_management.count(),
                "ai": self.store.rpt_ai_insights.count(),
            },
            "kpi": {
                "kpis": self.store.rpt_kpis.count(),
                "analytics": self.store.rpt_analytics.count(),
            },
            "profitability": {
                "analytics": self.store.rpt_analytics.count(),
                "management": self.store.rpt_management.count(),
            },
            "forecast": {
                "forecasts": self.store.rpt_forecasts.count(),
                "scenarios": self.store.rpt_scenarios.count(),
                "sensitivity": self.store.rpt_sensitivity.count(),
            },
            "enterprise_bi": {
                "consolidations": self.store.rpt_consolidations.count(),
                "statements": self.store.rpt_statements.count(),
                "kpis": self.store.rpt_kpis.count(),
                "forecasts": self.store.rpt_forecasts.count(),
            },
        }[dashboard_type]
        did = _id("rpt_dash")
        return self.store.rpt_dashboards.save(
            did,
            {
                "dashboard_id": did,
                "dashboard_type": dashboard_type,
                "metrics": metrics,
                "generated_at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.rpt_dashboards.count(), "types": self.types}
