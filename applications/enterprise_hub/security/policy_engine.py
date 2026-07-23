"""Policy engine — IP, time, geo, device, role, company policies."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.security.models import POLICY_KINDS
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class PolicyEngine:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def create(
        self,
        *,
        kind: str,
        name: str,
        rule: dict[str, Any] | None = None,
        company_id: str = "",
    ) -> dict[str, Any]:
        k = kind.lower().strip()
        if k not in POLICY_KINDS:
            raise ValidationError(f"kind must be one of {list(POLICY_KINDS)}")
        if not name:
            raise ValidationError("name required")
        pid = _id("isam_pol")
        return self.store.isam_policies.save(
            pid,
            {
                "policy_id": pid,
                "kind": k,
                "name": name,
                "rule": rule or {},
                "company_id": company_id,
                "enabled": True,
                "at": _now(),
            },
        )

    def evaluate(self, *, policy_id: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        policy = self.store.isam_policies.get(policy_id)
        if policy is None:
            from applications.enterprise_hub.shared.exceptions import NotFoundError

            raise NotFoundError(f"policy not found: {policy_id}")
        ctx = context or {}
        allowed = True
        rule = policy.get("rule") or {}
        if policy["kind"] == "ip" and rule.get("allowlist"):
            allowed = ctx.get("ip") in rule["allowlist"]
        elif policy["kind"] == "device" and rule.get("trusted"):
            allowed = ctx.get("device") in rule["trusted"]
        eid = _id("isam_peval")
        return self.store.isam_policy_evals.save(
            eid,
            {
                "evaluation_id": eid,
                "policy_id": policy_id,
                "allowed": allowed,
                "context": ctx,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "policies": self.store.isam_policies.count(),
            "evaluations": self.store.isam_policy_evals.count(),
            "kinds": list(POLICY_KINDS),
        }
