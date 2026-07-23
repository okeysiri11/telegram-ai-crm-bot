"""Dashboards and knowledge for Judicial Intelligence."""

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


class JudicialDashboard:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.types = list(DEFAULT_CONFIG.ji_dashboard_types)

    def render(self, *, dashboard_type: str = "court") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "court": {
                "decisions": self.store.ji_decisions.count(),
                "courts": len({d.get("court_name") for d in self.store.ji_decisions.list_all()}),
            },
            "decision": {
                "judgments": self.store.ji_judgments.count(),
                "rulings": self.store.ji_rulings.count(),
                "orders": self.store.ji_orders.count(),
                "opinions": self.store.ji_opinions.count(),
            },
            "judge": {
                "judges": self.store.ji_judges.count(),
                "history": self.store.ji_judge_history.count(),
                "workload": self.store.ji_workload.count(),
            },
            "ai_judicial": {
                "analyses": self.store.ji_analyses.count(),
                "searches": self.store.ji_searches.count(),
                "conflicts": self.store.ji_conflicts.count(),
            },
        }[dashboard_type]
        did = _id("ji_dash")
        return self.store.ji_dashboards.save(
            did,
            {
                "dashboard_id": did,
                "dashboard_type": dashboard_type,
                "metrics": metrics,
                "generated_at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.ji_dashboards.count(), "types": self.types}


class JudicialKnowledge:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.types = list(DEFAULT_CONFIG.ji_knowledge_bases)

    def publish(self, *, base: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if base not in self.types:
            raise ValidationError(f"base must be one of {self.types}")
        if not key:
            raise ValidationError("key required")
        rid = _id("ji_kg")
        return self.store.ji_knowledge.save(
            rid,
            {
                "entry_id": rid,
                "base": base,
                "key": key,
                "payload": payload or {},
                "graph_node": f"ji:{base}:{key}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "entries": self.store.ji_knowledge.count(),
            "bases": self.types,
            "decisions": self.store.ji_decisions.count(),
            "judges": self.store.ji_judges.count(),
            "citations": self.store.ji_citations.count(),
        }
