"""Dashboards for AI Legal Assistant."""

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


class AILegalAssistantDashboard:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.types = list(DEFAULT_CONFIG.aa_dashboard_types)

    def render(self, *, dashboard_type: str = "assistant") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "assistant": {
                "conversations": self.store.aa_conversations.count(),
                "messages": self.store.aa_messages.count(),
                "workspaces": self.store.aa_workspaces.count(),
            },
            "research": {
                "searches": self.store.aa_searches.count(),
                "citations": self.store.aa_citations.count(),
                "authorities": self.store.aa_authorities.count(),
            },
            "knowledge": {
                "entries": self.store.aa_knowledge.count(),
                "concepts": self.store.aa_concepts.count(),
                "entities": self.store.aa_entities.count(),
            },
            "intelligence": {
                "analyses": self.store.aa_analyses.count(),
                "opinions": self.store.aa_opinions.count(),
                "explanations": self.store.aa_explanations.count(),
            },
        }[dashboard_type]
        did = _id("aa_dash")
        return self.store.aa_dashboards.save(
            did,
            {
                "dashboard_id": did,
                "dashboard_type": dashboard_type,
                "metrics": metrics,
                "generated_at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.aa_dashboards.count(), "types": self.types}
