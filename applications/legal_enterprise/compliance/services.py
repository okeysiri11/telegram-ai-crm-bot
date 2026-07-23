"""Dashboards and knowledge for Compliance Platform."""

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


class ComplianceDashboard:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.types = list(DEFAULT_CONFIG.cp_dashboard_types)

    def render(self, *, dashboard_type: str = "compliance") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "compliance": {
                "frameworks": self.store.cp_frameworks.count(),
                "checklists": self.store.cp_checklists.count(),
                "policies": self.store.cp_policies.count(),
            },
            "corporate": {
                "companies": self.store.cp_companies.count(),
                "board": self.store.cp_board.count(),
                "resolutions": self.store.cp_resolutions.count(),
            },
            "license": {
                "licenses": self.store.cp_licenses.count(),
                "renewals": self.store.cp_renewals.count(),
                "expirations": self.store.cp_expirations.count(),
            },
            "risk": {
                "risks": self.store.cp_risks.count(),
                "aml_scores": self.store.cp_aml_scores.count(),
                "high_risk": self.store.cp_high_risk.count(),
            },
            "ai_compliance": {
                "insights": self.store.cp_ai_insights.count(),
                "counterparties": self.store.cp_counterparties.count(),
            },
        }[dashboard_type]
        did = _id("cp_dash")
        return self.store.cp_dashboards.save(
            did,
            {
                "dashboard_id": did,
                "dashboard_type": dashboard_type,
                "metrics": metrics,
                "generated_at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.cp_dashboards.count(), "types": self.types}


class ComplianceKnowledge:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.types = list(DEFAULT_CONFIG.cp_knowledge_bases)

    def publish(self, *, base: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if base not in self.types:
            raise ValidationError(f"base must be one of {self.types}")
        if not key:
            raise ValidationError("key required")
        rid = _id("cp_kg")
        return self.store.cp_knowledge.save(
            rid,
            {
                "entry_id": rid,
                "base": base,
                "key": key,
                "payload": payload or {},
                "graph_node": f"cp:{base}:{key}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "entries": self.store.cp_knowledge.count(),
            "bases": self.types,
            "companies": self.store.cp_companies.count(),
            "licenses": self.store.cp_licenses.count(),
            "policies": self.store.cp_policies.count(),
            "risks": self.store.cp_risks.count(),
        }
