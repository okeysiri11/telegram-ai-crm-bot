"""AI decision support — recommendations and strategic priority ranking."""

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


class DecisionSupport:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.rec_types = list(DEFAULT_CONFIG.cfo_recommendation_types)

    def recommend(
        self,
        *,
        recommendation_type: str,
        subject: str,
        priority: int = 1,
        score: float = 0.75,
        detail: str = "",
    ) -> dict[str, Any]:
        rt = recommendation_type.lower().strip()
        if rt not in self.rec_types:
            raise ValidationError(f"recommendation_type must be one of {self.rec_types}")
        if not subject:
            raise ValidationError("subject required")
        rid = _id("cfo_rec")
        return self.store.cfo_recommendations.save(
            rid,
            {
                "recommendation_id": rid,
                "recommendation_type": rt,
                "subject": subject,
                "priority": int(priority),
                "score": max(0.0, min(1.0, float(score))),
                "detail": detail or f"{rt.replace('_', ' ')} for {subject}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "recommendations": self.store.cfo_recommendations.count(),
            "types": self.rec_types,
        }
