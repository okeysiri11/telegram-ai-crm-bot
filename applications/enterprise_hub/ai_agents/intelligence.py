"""AI intelligence — optimization, feedback, recommendations, knowledge reuse, context decisions."""

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


class AgentIntelligence:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.insight_types = list(DEFAULT_CONFIG.aa_intel_types)

    def insight(
        self,
        *,
        insight_type: str,
        subject: str,
        detail: str = "",
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        it = insight_type.lower().strip()
        if it not in self.insight_types:
            raise ValidationError(f"insight_type must be one of {self.insight_types}")
        if not subject:
            raise ValidationError("subject required")
        iid = _id("aa_intel")
        return self.store.aa_insights.save(
            iid,
            {
                "insight_id": iid,
                "insight_type": it,
                "subject": subject,
                "detail": detail,
                "payload": payload or {},
                "at": _now(),
            },
        )

    def feedback(self, *, agent_id: str, outcome: str, score: float = 1.0) -> dict[str, Any]:
        if not agent_id or not outcome:
            raise ValidationError("agent_id and outcome required")
        fid = _id("aa_fb")
        return self.store.aa_feedback.save(
            fid,
            {
                "feedback_id": fid,
                "agent_id": agent_id,
                "outcome": outcome,
                "score": float(score),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "insights": self.store.aa_insights.count(),
            "feedback": self.store.aa_feedback.count(),
            "insight_types": self.insight_types,
        }
