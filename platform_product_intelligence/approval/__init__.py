"""Owner Approval Center — Sprint 22.0."""

from __future__ import annotations

from typing import Any

from platform_product_intelligence.models import APPROVED_DECISIONS, OWNER_DECISIONS


class OwnerApprovalCenter:
    def decide(
        self,
        *,
        decision: str,
        owner_id: str,
        changes: str = "",
        notes: str = "",
    ) -> dict[str, Any]:
        if not owner_id or not str(owner_id).strip():
            raise ValueError("owner_id is required")
        if decision not in OWNER_DECISIONS:
            raise ValueError(f"invalid owner decision: {decision}")
        development_allowed = decision in APPROVED_DECISIONS
        return {
            "decision": decision,
            "owner_id": owner_id.strip(),
            "changes": changes,
            "notes": notes,
            "development_allowed": development_allowed,
            "ai_may_start_development": False,
            "status": "approved" if development_allowed else decision,
        }

    def decisions(self) -> list[str]:
        return list(OWNER_DECISIONS)
