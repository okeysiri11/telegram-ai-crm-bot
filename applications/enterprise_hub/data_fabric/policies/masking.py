from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class MaskingPolicy:
    KIND = "masking"

    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def apply(self, *, asset_id: str, rules: dict[str, Any] | None = None, principal: str = "system") -> dict[str, Any]:
        if not asset_id:
            raise ValidationError("asset_id is required")
        pid = _id("edf_pol")
        return self.store.edf_policies.save(
            pid,
            {
                "policy_id": pid,
                "kind": self.KIND,
                "asset_id": asset_id,
                "principal": principal,
                "rules": rules or {},
                "applied_at": _now(),
                "status": "active",
            },
        )

    def evaluate(self, *, policy_id: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        pol = self.store.edf_policies.get(policy_id)
        if not pol:
            raise NotFoundError(f"policy not found: {policy_id}")
        allowed = True
        reasons: list[str] = []
        if self.KIND == "access" and (context or {}).get("denied"):
            allowed = False
            reasons.append("access denied by policy")
        return {"policy_id": policy_id, "kind": self.KIND, "allowed": allowed, "reasons": reasons, "policy": pol}

    def status(self) -> dict[str, Any]:
        items = [p for p in self.store.edf_policies.list_all() if p.get("kind") == self.KIND]
        return {"kind": self.KIND, "policies": len(items)}
