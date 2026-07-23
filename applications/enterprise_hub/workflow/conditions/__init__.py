"""Workflow conditions — user, role, time, status, variable, AI."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store
from applications.enterprise_hub.workflow.models import CONDITION_TYPES


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def evaluate_condition(
    *,
    condition_type: str,
    expected: Any,
    actual: Any = None,
    context: dict[str, Any] | None = None,
) -> bool:
    ct = condition_type.lower().strip()
    ctx = context or {}
    if ct == "user":
        return str(actual or ctx.get("user", "")) == str(expected)
    if ct == "role":
        return str(actual or ctx.get("role", "")) == str(expected)
    if ct == "status":
        return str(actual or ctx.get("status", "")) == str(expected)
    if ct == "project":
        return str(actual or ctx.get("project", "")) == str(expected)
    if ct == "module":
        return str(actual or ctx.get("module", "")) == str(expected)
    if ct == "field":
        field = str(expected)
        return bool(ctx.get(field))
    if ct in ("date", "time"):
        return True
    if ct == "ai_decision":
        return str(actual or ctx.get("ai_decision", "approve")).lower() in (
            "approve",
            "true",
            "yes",
            str(expected).lower(),
        )
    if ct == "expression":
        return bool(expected)
    return False


class ConditionEngine:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def check(
        self,
        *,
        condition_type: str,
        expected: Any = None,
        actual: Any = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        ct = condition_type.lower().strip()
        if ct not in CONDITION_TYPES:
            raise ValidationError(f"condition_type must be one of {list(CONDITION_TYPES)}")
        passed = evaluate_condition(
            condition_type=ct, expected=expected, actual=actual, context=context
        )
        cid = _id("wf_cond")
        return self.store.wf_conditions.save(
            cid,
            {
                "condition_id": cid,
                "condition_type": ct,
                "expected": expected,
                "actual": actual,
                "passed": passed,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"checks": self.store.wf_conditions.count(), "types": list(CONDITION_TYPES)}
