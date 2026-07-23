"""Policy engine — collaboration, limits, priority, cost/quality routing."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.ai_orchestrator.models import POLICY_KINDS
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class PolicyEngine:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def define(
        self,
        *,
        kind: str,
        name: str,
        rules: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        k = kind.lower().strip()
        if k not in POLICY_KINDS:
            raise ValidationError(f"kind must be one of {list(POLICY_KINDS)}")
        if not name:
            raise ValidationError("name is required")
        pid = _id("aop_pol")
        return self.store.aop_policies.save(
            pid,
            {
                "policy_id": pid,
                "kind": k,
                "name": name.strip(),
                "rules": rules or {},
                "active": True,
                "at": _now(),
            },
        )

    def evaluate(self, *, strategy: str, estimated_cost: float = 0.0) -> dict[str, Any]:
        policies = self.store.aop_policies.list_all()
        allowed = True
        notes = []
        for p in policies:
            if p.get("kind") == "cost_quality" and estimated_cost > float(
                (p.get("rules") or {}).get("max_cost", 1e9)
            ):
                allowed = False
                notes.append(f"blocked by {p['name']}: cost")
            if p.get("kind") == "collaboration":
                allowed_strategies = (p.get("rules") or {}).get("strategies") or []
                if allowed_strategies and strategy not in allowed_strategies:
                    notes.append(f"strategy hint from {p['name']}")
        eid = _id("aop_pev")
        return self.store.aop_policy_evals.save(
            eid,
            {
                "eval_id": eid,
                "strategy": strategy,
                "estimated_cost": estimated_cost,
                "allowed": allowed,
                "notes": notes,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"policies": self.store.aop_policies.count(), "kinds": list(POLICY_KINDS)}
