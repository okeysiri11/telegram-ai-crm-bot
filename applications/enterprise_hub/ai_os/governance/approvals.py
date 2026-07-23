"""Approval gates."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class ApprovalGate:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def require(self, *, goal_id: str, reason: str = "high risk") -> dict[str, Any]:
        aid = _id("aios_apr")
        return self.store.aios_approvals.save(
            aid,
            {
                "approval_id": aid,
                "goal_id": goal_id,
                "reason": reason,
                "status": "pending",
                "at": _now(),
            },
        )

    def approve(self, *, approval_id: str, actor: str = "user") -> dict[str, Any]:
        from applications.enterprise_hub.shared.exceptions import NotFoundError

        item = self.store.aios_approvals.get(approval_id)
        if not item:
            raise NotFoundError(f"approval not found: {approval_id}")
        item["status"] = "approved"
        item["actor"] = actor
        item["approved_at"] = _now()
        return self.store.aios_approvals.save(approval_id, item)
