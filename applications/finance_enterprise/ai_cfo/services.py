"""AI CFO dashboards and knowledge graph."""

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


class AICFOKnowledge:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.bases = list(DEFAULT_CONFIG.cfo_knowledge_bases)

    def publish(self, *, base: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if base not in self.bases:
            raise ValidationError(f"base must be one of {self.bases}")
        if not key:
            raise ValidationError("key required")
        eid = _id("cfo_kg")
        return self.store.cfo_knowledge.save(
            eid,
            {
                "entry_id": eid,
                "base": base,
                "key": key,
                "payload": payload or {},
                "graph_node": f"cfo:{base}:{key}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"entries": self.store.cfo_knowledge.count(), "bases": self.bases}


class AICFODashboard:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.types = list(DEFAULT_CONFIG.cfo_dashboard_types)

    def render(self, *, dashboard_type: str = "ai_cfo") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "ai_cfo": {
                "workspaces": self.store.cfo_workspaces.count(),
                "conversations": self.store.cfo_conversations.count(),
                "recommendations": self.store.cfo_recommendations.count(),
            },
            "financial_health": {
                "performance": self.store.cfo_performance.count(),
                "risks": self.store.cfo_risks.count(),
            },
            "investment": {
                "strategies": self.store.cfo_strategies.count(),
                "models": self.store.cfo_models.count(),
            },
            "risk": {
                "risks": self.store.cfo_risks.count(),
                "mitigations": self.store.cfo_risks.count(),
            },
            "strategy": {
                "strategies": self.store.cfo_strategies.count(),
                "recommendations": self.store.cfo_recommendations.count(),
                "reports": self.store.cfo_reports.count(),
            },
        }[dashboard_type]
        did = _id("cfo_dash")
        return self.store.cfo_dashboards.save(
            did,
            {
                "dashboard_id": did,
                "dashboard_type": dashboard_type,
                "metrics": metrics,
                "generated_at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.cfo_dashboards.count(), "types": self.types}
