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



from applications.enterprise_hub.data_fabric.policies.access import AccessPolicy
from applications.enterprise_hub.data_fabric.policies.encryption import EncryptionPolicy
from applications.enterprise_hub.data_fabric.policies.masking import MaskingPolicy
from applications.enterprise_hub.data_fabric.policies.retention import RetentionPolicy


class DataGovernance:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.access = AccessPolicy(self.store)
        self.retention = RetentionPolicy(self.store)
        self.masking = MaskingPolicy(self.store)
        self.encryption = EncryptionPolicy(self.store)

    def enforce(
        self,
        *,
        asset_id: str,
        principal: str = "system",
        retain_days: int = 365,
        mask_fields: list[str] | None = None,
    ) -> dict[str, Any]:
        a = self.access.apply(asset_id=asset_id, principal=principal, rules={"roles": ["reader"]})
        r = self.retention.apply(asset_id=asset_id, rules={"retain_days": retain_days})
        m = self.masking.apply(asset_id=asset_id, rules={"fields": list(mask_fields or ["ssn", "email"])})
        e = self.encryption.apply(asset_id=asset_id, rules={"algorithm": "AES-256"})
        gid = _id("edf_gov")
        return self.store.edf_governance.save(
            gid,
            {
                "governance_id": gid,
                "asset_id": asset_id,
                "access_policy_id": a["policy_id"],
                "retention_policy_id": r["policy_id"],
                "masking_policy_id": m["policy_id"],
                "encryption_policy_id": e["policy_id"],
                "at": _now(),
            },
        )

    def audit(self, *, asset_id: str, action: str, principal: str = "system") -> dict[str, Any]:
        aid = _id("edf_gaud")
        return self.store.edf_gov_audit.save(
            aid,
            {"audit_id": aid, "asset_id": asset_id, "action": action, "principal": principal, "at": _now()},
        )

    def status(self) -> dict[str, Any]:
        return {
            "enforcements": len(self.store.edf_governance.list_all()),
            "audit_events": len(self.store.edf_gov_audit.list_all()),
            "policies": len(self.store.edf_policies.list_all()),
        }
