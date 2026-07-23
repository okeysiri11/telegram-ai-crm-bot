"""Dashboards and knowledge for Legislation Intelligence."""

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


class LegislationIntelligenceDashboard:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.types = list(DEFAULT_CONFIG.li_dashboard_types)

    def render(self, *, dashboard_type: str = "legislation") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "legislation": {
                "constitutions": self.store.li_constitutions.count(),
                "codes": self.store.li_codes.count(),
                "laws": self.store.li_laws.count(),
                "articles": self.store.li_articles.count(),
            },
            "regulation": {
                "regulations": self.store.li_regulations.count(),
                "resolutions": self.store.li_resolutions.count(),
                "orders": self.store.li_orders.count(),
                "local": self.store.li_local_regs.count(),
            },
            "legal_search": {
                "searches": self.store.li_searches.count(),
                "cross_refs": self.store.li_cross_refs.count(),
            },
            "ai_analysis": {
                "analyses": self.store.li_analyses.count(),
                "classifications": self.store.li_classifications.count(),
                "conflicts": self.store.li_conflicts.count(),
            },
        }[dashboard_type]
        did = _id("li_dash")
        return self.store.li_dashboards.save(
            did,
            {
                "dashboard_id": did,
                "dashboard_type": dashboard_type,
                "metrics": metrics,
                "generated_at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.li_dashboards.count(), "types": self.types}


class LegislationIntelligenceKnowledge:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.types = list(DEFAULT_CONFIG.li_knowledge_bases)

    def publish(self, *, base: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if base not in self.types:
            raise ValidationError(f"base must be one of {self.types}")
        if not key:
            raise ValidationError("key required")
        rid = _id("li_kg")
        return self.store.li_knowledge.save(
            rid,
            {
                "entry_id": rid,
                "base": base,
                "key": key,
                "payload": payload or {},
                "graph_node": f"li:{base}:{key}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "entries": self.store.li_knowledge.count(),
            "bases": self.types,
            "articles": self.store.li_articles.count(),
            "references": self.store.li_cross_refs.count(),
            "regulations": self.store.li_regulations.count(),
        }
