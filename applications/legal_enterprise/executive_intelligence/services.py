"""Knowledge graph and executive dashboards."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.legal_enterprise.config import DEFAULT_CONFIG
from applications.legal_enterprise.shared.exceptions import ValidationError
from applications.legal_enterprise.shared.store import LegalEnterpriseStore, legal_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class ExecutiveKnowledge:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.bases = list(DEFAULT_CONFIG.ei_knowledge_bases)

    def publish(self, *, base: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if base not in self.bases:
            raise ValidationError(f"base must be one of {self.bases}")
        if not key:
            raise ValidationError("key required")
        eid = _id("ei_kg")
        return self.store.ei_knowledge.save(
            eid,
            {
                "entry_id": eid,
                "base": base,
                "key": key,
                "payload": payload or {},
                "graph_node": f"ei:{base}:{key}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"entries": self.store.ei_knowledge.count(), "bases": self.bases}


class ExecutiveIntelligenceDashboard:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.types = list(DEFAULT_CONFIG.ei_dashboard_types)

    def render(self, *, dashboard_type: str = "executive") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "executive": {
                "snapshots": self.store.ei_overview.count(),
                "alerts": self.store.ei_alerts.count(),
                "reports": self.store.ei_reports.count(),
            },
            "risk": {
                "scores": self.store.ei_risks.count(),
                "forecasts": self.store.ei_risk_forecasts.count(),
            },
            "forecast": {
                "regulatory": self.store.ei_forecasts.count(),
                "risk_forecasts": self.store.ei_risk_forecasts.count(),
            },
            "strategy": {
                "recommendations": self.store.ei_recommendations.count(),
                "qa": self.store.ei_qa.count(),
            },
            "operations": {
                "analytics": self.store.ei_analytics.count(),
                "knowledge": self.store.ei_knowledge.count(),
            },
        }[dashboard_type]
        did = _id("ei_dash")
        return self.store.ei_dashboards.save(
            did,
            {
                "dashboard_id": did,
                "dashboard_type": dashboard_type,
                "metrics": metrics,
                "generated_at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.ei_dashboards.count(), "types": self.types}
