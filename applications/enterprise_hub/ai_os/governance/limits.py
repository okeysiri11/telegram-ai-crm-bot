"""Budget and time limits."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class LimitsPolicy:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def define(self, *, max_budget: float = 10.0, max_minutes: int = 60) -> dict[str, Any]:
        lid = _id("aios_lim")
        return self.store.aios_limits.save(
            lid,
            {
                "limit_id": lid,
                "max_budget": float(max_budget),
                "max_minutes": int(max_minutes),
                "at": _now(),
            },
        )

    def check(self, *, spent: float, budget: float) -> dict[str, Any]:
        return {"allowed": spent <= budget, "spent": spent, "budget": budget}
