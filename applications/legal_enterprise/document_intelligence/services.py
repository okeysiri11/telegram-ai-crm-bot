"""Dashboards and knowledge for Document Intelligence."""

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


class DocumentIntelligenceDashboard:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.types = list(DEFAULT_CONFIG.di_dashboard_types)

    def render(self, *, dashboard_type: str = "contract") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "contract": {
                "contracts": self.store.di_contracts.count(),
                "templates": self.store.di_templates.count(),
                "clauses": self.store.di_clause_library.count(),
            },
            "document": {
                "documents": self.store.di_documents.count(),
                "ocr": self.store.di_ocr.count(),
                "parses": self.store.di_parses.count(),
            },
            "risk": {
                "reviews": self.store.di_risks.count(),
                "comparisons": self.store.di_comparisons.count(),
            },
            "ai_review": {
                "drafts": self.store.di_drafts.count(),
                "risks": self.store.di_risks.count(),
                "redlines": self.store.di_redlines.count(),
            },
        }[dashboard_type]
        did = _id("di_dash")
        return self.store.di_dashboards.save(
            did,
            {
                "dashboard_id": did,
                "dashboard_type": dashboard_type,
                "metrics": metrics,
                "generated_at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.di_dashboards.count(), "types": self.types}


class DocumentIntelligenceKnowledge:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.types = list(DEFAULT_CONFIG.di_knowledge_bases)

    def publish(self, *, base: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if base not in self.types:
            raise ValidationError(f"base must be one of {self.types}")
        if not key:
            raise ValidationError("key required")
        rid = _id("di_kg")
        return self.store.di_knowledge.save(
            rid,
            {
                "entry_id": rid,
                "base": base,
                "key": key,
                "payload": payload or {},
                "graph_node": f"di:{base}:{key}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "entries": self.store.di_knowledge.count(),
            "bases": self.types,
            "contracts": self.store.di_contracts.count(),
            "clauses": self.store.di_clause_library.count(),
            "risks": self.store.di_risks.count(),
            "templates": self.store.di_templates.count(),
        }
