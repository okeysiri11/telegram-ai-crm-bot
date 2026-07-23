"""Decision support — recommendations, priorities, strategies, scenarios."""

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


class DecisionSupport:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.kinds = list(DEFAULT_CONFIG.ei_decision_kinds)

    def recommend(
        self,
        *,
        kind: str,
        title: str,
        body: str = "",
        priority: str = "medium",
        items: list[str] | None = None,
    ) -> dict[str, Any]:
        k = kind.lower().strip()
        if k not in self.kinds:
            raise ValidationError(f"kind must be one of {self.kinds}")
        if not title:
            raise ValidationError("title required")
        rid = _id("ei_rec")
        return self.store.ei_recommendations.save(
            rid,
            {
                "recommendation_id": rid,
                "kind": k,
                "title": title,
                "body": body or f"{k.replace('_', ' ').title()}: {title}",
                "priority": priority,
                "items": items or [],
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"recommendations": self.store.ei_recommendations.count(), "kinds": self.kinds}
