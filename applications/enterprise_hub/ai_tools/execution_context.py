"""Execution context — agent, user, tool, params, result, cost."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.ai_tools.models import EXECUTION_STATUSES
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class ExecutionContext:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def open(
        self,
        *,
        tool_id: str,
        agent_id: str = "system",
        user_id: str = "system",
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        cid = _id("ats_ctx")
        return self.store.ats_contexts.save(
            cid,
            {
                "context_id": cid,
                "tool_id": tool_id,
                "agent_id": agent_id,
                "user_id": user_id,
                "params": params or {},
                "status": "pending",
                "result": None,
                "duration_ms": 0,
                "cost": 0.0,
                "log": [],
                "opened_at": _now(),
            },
        )

    def get(self, context_id: str) -> dict[str, Any]:
        item = self.store.ats_contexts.get(context_id)
        if not item:
            raise NotFoundError(f"context not found: {context_id}")
        return item

    def finalize(
        self,
        *,
        context_id: str,
        status: str,
        result: Any = None,
        duration_ms: int = 0,
        cost: float = 0.0,
        note: str = "",
    ) -> dict[str, Any]:
        ctx = self.get(context_id)
        st = status.lower().strip()
        if st not in EXECUTION_STATUSES:
            raise ValidationError(f"status must be one of {list(EXECUTION_STATUSES)}")
        ctx["status"] = st
        ctx["result"] = result
        ctx["duration_ms"] = int(duration_ms)
        ctx["cost"] = float(cost)
        if note:
            ctx.setdefault("log", []).append({"note": note, "at": _now()})
        ctx["closed_at"] = _now()
        return self.store.ats_contexts.save(context_id, ctx)
