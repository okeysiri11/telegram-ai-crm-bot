"""Dashboards and knowledge for Case Management Platform."""

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


class CaseManagementDashboard:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.types = list(DEFAULT_CONFIG.cm_dashboard_types)

    def render(self, *, dashboard_type: str = "case") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "case": {
                "cases": self.store.cm_cases.count(),
                "related": self.store.cm_related.count(),
                "ownership": self.store.cm_ownership.count(),
            },
            "calendar": {
                "hearings": self.store.cm_hearings.count(),
                "reminders": self.store.cm_reminders.count(),
                "courtrooms": self.store.cm_courtrooms.count(),
            },
            "deadline": {
                "deadlines": self.store.cm_deadlines.count(),
                "alerts": self.store.cm_deadline_alerts.count(),
            },
            "workflow": {
                "tasks": self.store.cm_tasks.count(),
                "workflows": self.store.cm_workflows.count(),
                "approvals": self.store.cm_approvals.count(),
            },
            "ai_case": {
                "insights": self.store.cm_ai_insights.count(),
                "documents": self.store.cm_documents.count(),
            },
        }[dashboard_type]
        did = _id("cm_dash")
        return self.store.cm_dashboards.save(
            did,
            {
                "dashboard_id": did,
                "dashboard_type": dashboard_type,
                "metrics": metrics,
                "generated_at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.cm_dashboards.count(), "types": self.types}


class CaseManagementKnowledge:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.types = list(DEFAULT_CONFIG.cm_knowledge_bases)

    def publish(self, *, base: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if base not in self.types:
            raise ValidationError(f"base must be one of {self.types}")
        if not key:
            raise ValidationError("key required")
        rid = _id("cm_kg")
        return self.store.cm_knowledge.save(
            rid,
            {
                "entry_id": rid,
                "base": base,
                "key": key,
                "payload": payload or {},
                "graph_node": f"cm:{base}:{key}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "entries": self.store.cm_knowledge.count(),
            "bases": self.types,
            "cases": self.store.cm_cases.count(),
            "deadlines": self.store.cm_deadlines.count(),
            "tasks": self.store.cm_tasks.count(),
            "documents": self.store.cm_documents.count(),
            "hearings": self.store.cm_hearings.count(),
        }
