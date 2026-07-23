"""Risk analysis scoring."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class RiskAnalyzer:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def score(self, *, subject: str, factors: dict[str, float] | None = None) -> dict[str, Any]:
        if not subject:
            raise ValidationError("subject required")
        f = factors or {}
        value = min(1.0, sum(float(v) for v in f.values()) / max(1, len(f) or 1))
        level = "low" if value < 0.3 else "medium" if value < 0.7 else "high"
        rid = _id("isam_risk")
        return self.store.isam_risks.save(
            rid,
            {
                "risk_id": rid,
                "subject": subject,
                "score": value,
                "level": level,
                "factors": f,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"scores": self.store.isam_risks.count()}
