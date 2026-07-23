"""AI decision engine — strategy, platform selection, optimization, conflict, validate."""

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


class AIDecisionEngine:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.decision_types = list(DEFAULT_CONFIG.orch_decision_types)

    def decide(
        self,
        *,
        decision_type: str,
        subject: str,
        selected: str = "",
        score: float = 0.8,
        detail: str = "",
    ) -> dict[str, Any]:
        dt = decision_type.lower().strip()
        if dt not in self.decision_types:
            raise ValidationError(f"decision_type must be one of {self.decision_types}")
        if not subject:
            raise ValidationError("subject required")
        did = _id("orch_dec")
        return self.store.orch_decisions.save(
            did,
            {
                "decision_id": did,
                "decision_type": dt,
                "subject": subject,
                "selected": selected or subject,
                "score": max(0.0, min(1.0, float(score))),
                "detail": detail or f"{dt.replace('_', ' ')} for {subject}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "decisions": self.store.orch_decisions.count(),
            "types": self.decision_types,
        }
