"""AI explainability — reasoning, decision trace, summary, confidence, NL explanation."""

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


class AIExplainability:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.explain_types = list(DEFAULT_CONFIG.orch_explain_types)

    def explain(
        self,
        *,
        explain_type: str,
        subject: str,
        confidence: float = 0.85,
        narrative: str = "",
    ) -> dict[str, Any]:
        et = explain_type.lower().strip()
        if et not in self.explain_types:
            raise ValidationError(f"explain_type must be one of {self.explain_types}")
        if not subject:
            raise ValidationError("subject required")
        eid = _id("orch_xpl")
        text = narrative or (
            f"{et.replace('_', ' ').title()} for {subject}: "
            f"{self.store.orch_decisions.count()} decisions, "
            f"{self.store.orch_executions.count()} executions."
        )
        return self.store.orch_explanations.save(
            eid,
            {
                "explanation_id": eid,
                "explain_type": et,
                "subject": subject,
                "confidence": max(0.0, min(1.0, float(confidence))),
                "narrative": text,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "explanations": self.store.orch_explanations.count(),
            "types": self.explain_types,
        }
