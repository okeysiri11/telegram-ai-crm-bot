"""AI knowledge intelligence — recommendations, reasoning, correlation, NL queries."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class KnowledgeAI:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.insight_types = list(DEFAULT_CONFIG.kg_ai_insight_types)

    def insight(
        self,
        *,
        insight_type: str,
        subject: str,
        score: float = 0.8,
        detail: str = "",
    ) -> dict[str, Any]:
        it = insight_type.lower().strip()
        if it not in self.insight_types:
            raise ValidationError(f"insight_type must be one of {self.insight_types}")
        if not subject:
            raise ValidationError("subject required")
        iid = _id("kg_ai")
        return self.store.kg_ai_insights.save(
            iid,
            {
                "insight_id": iid,
                "insight_type": it,
                "subject": subject,
                "score": max(0.0, min(1.0, float(score))),
                "detail": detail or f"{it.replace('_', ' ')} for {subject}",
                "at": _now(),
            },
        )

    def nl_query(self, *, question: str, audience: str = "executive") -> dict[str, Any]:
        if not question:
            raise ValidationError("question required")
        entities = self.store.kg_entities.count()
        memories = self.store.kg_memories.count()
        narrative = (
            f"Knowledge answer for {audience}: '{question}'. "
            f"Graph has {entities} entities and {memories} memories."
        )
        return self.insight(
            insight_type="nl_query",
            subject=audience,
            score=0.88,
            detail=narrative,
        )

    def status(self) -> dict[str, Any]:
        return {
            "insights": self.store.kg_ai_insights.count(),
            "types": self.insight_types,
        }
