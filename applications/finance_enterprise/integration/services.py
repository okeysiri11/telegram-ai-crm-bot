"""Integration dashboards and knowledge graph."""

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


class IntegrationKnowledge:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.bases = list(DEFAULT_CONFIG.int_knowledge_bases)

    def publish(self, *, base: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if base not in self.bases:
            raise ValidationError(f"base must be one of {self.bases}")
        if not key:
            raise ValidationError("key required")
        eid = _id("int_kg")
        return self.store.int_knowledge.save(
            eid,
            {
                "entry_id": eid,
                "base": base,
                "key": key,
                "payload": payload or {},
                "graph_node": f"int:{base}:{key}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"entries": self.store.int_knowledge.count(), "bases": self.bases}


class IntegrationDashboard:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.types = list(DEFAULT_CONFIG.int_dashboard_types)

    def render(self, *, dashboard_type: str = "enterprise_finance") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "enterprise_finance": {
                "events": self.store.int_events.count(),
                "operations": self.store.int_operations.count(),
                "analytics": self.store.int_analytics.count(),
            },
            "cross_platform": {
                "operations": self.store.int_operations.count(),
                "dependencies": self.store.int_dependencies.count(),
                "routes": self.store.int_routes.count(),
            },
            "operations": {
                "operations": self.store.int_operations.count(),
                "logs": self.store.int_event_logs.count(),
            },
            "revenue": {
                "analytics": self.store.int_analytics.count(),
                "events": self.store.int_events.count(),
            },
            "executive_integration": {
                "ai": self.store.int_ai_insights.count(),
                "events": self.store.int_events.count(),
                "dependencies": self.store.int_dependencies.count(),
            },
        }[dashboard_type]
        did = _id("int_dash")
        return self.store.int_dashboards.save(
            did,
            {
                "dashboard_id": did,
                "dashboard_type": dashboard_type,
                "metrics": metrics,
                "generated_at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.int_dashboards.count(), "types": self.types}
