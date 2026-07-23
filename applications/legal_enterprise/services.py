"""Dashboards and Legal Knowledge Graph."""

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


class LegalDashboard:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.types = list(DEFAULT_CONFIG.dashboard_types)

    def render(self, *, dashboard_type: str = "legal") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "legal": {
                "entities": self.store.legal_entities.count(),
                "individuals": self.store.individuals.count(),
                "attorneys": self.store.attorneys.count(),
                "judges": self.store.judges.count(),
                "agencies": self.store.agencies.count(),
            },
            "case": {
                "cases": self.store.cases.count(),
                "documents": self.store.documents.count(),
                "evidence": self.store.evidence.count(),
                "tasks": self.store.tasks.count(),
            },
            "court": {
                "courts": self.store.courts.count(),
                "jurisdictions": self.store.jurisdictions.count(),
                "hierarchies": self.store.court_hierarchies.count(),
                "categories": self.store.case_categories.count(),
            },
            "legislation": {
                "constitutions": self.store.constitutions.count(),
                "codes": (
                    self.store.civil_codes.count()
                    + self.store.commercial_codes.count()
                    + self.store.criminal_codes.count()
                    + self.store.administrative_codes.count()
                    + self.store.tax_codes.count()
                    + self.store.labor_codes.count()
                ),
                "treaties": self.store.treaties.count(),
                "versions": self.store.legislation_versions.count(),
            },
        }[dashboard_type]
        did = _id("le_dash")
        return self.store.dashboards.save(
            did,
            {
                "dashboard_id": did,
                "dashboard_type": dashboard_type,
                "metrics": metrics,
                "generated_at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.dashboards.count(), "types": self.types}


class LegalKnowledge:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.types = list(DEFAULT_CONFIG.knowledge_bases)

    def publish(self, *, base: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if base not in self.types:
            raise ValidationError(f"base must be one of {self.types}")
        if not key:
            raise ValidationError("key required")
        rid = _id("le_kg")
        return self.store.knowledge.save(
            rid,
            {
                "entry_id": rid,
                "base": base,
                "key": key,
                "payload": payload or {},
                "graph_node": f"le:{base}:{key}",
                "at": _now(),
            },
        )

    def relate(
        self,
        *,
        from_base: str,
        from_key: str,
        to_base: str,
        to_key: str,
        relation: str = "related_to",
    ) -> dict[str, Any]:
        for base in (from_base, to_base):
            if base not in self.types:
                raise ValidationError(f"base must be one of {self.types}")
        if not from_key or not to_key:
            raise ValidationError("from_key and to_key required")
        rid = _id("le_rel")
        return self.store.relationships.save(
            rid,
            {
                "relationship_id": rid,
                "from": f"le:{from_base}:{from_key}",
                "to": f"le:{to_base}:{to_key}",
                "relation": relation,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "entries": self.store.knowledge.count(),
            "relationships": self.store.relationships.count(),
            "bases": self.types,
        }
