"""Owner approval for commercial actions — Sprint 22.1."""

from __future__ import annotations

from typing import Any

from platform_ai_business_advisor.models import OWNER_DECISIONS


class OwnerApproval:
    def decide(self, *, decision: str, owner_id: str, notes: str = "") -> dict[str, Any]:
        if not owner_id or not str(owner_id).strip():
            raise ValueError("owner_id is required")
        if decision not in OWNER_DECISIONS:
            raise ValueError(f"invalid owner decision: {decision}")
        execution_allowed = decision == "approve"
        return {
            "decision": decision,
            "owner_id": owner_id.strip(),
            "notes": notes,
            "execution_allowed": execution_allowed,
            "ai_may_execute": False,
            "status": "approved" if execution_allowed else decision,
        }
