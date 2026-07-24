"""Human Approval Node — Sprint 24.1."""

from __future__ import annotations

from typing import Any

from platform_workflow_intelligence.models import APPROVAL_KINDS


class HumanApprovalNode:
    def require(self, *, kind: str, actor: str = "") -> dict[str, Any]:
        kind = (kind or "").lower()
        if kind not in APPROVAL_KINDS:
            raise ValueError(f"unsupported approval: {kind}")
        return {
            "kind": kind,
            "actor": actor or None,
            "pending": True,
            "ai_recommendation_only": kind == "ai_recommendation",
            "blocks_critical": kind in ("owner_approval", "manager_approval"),
        }
