"""Data governance — retention, access, classification, audit, lifecycle."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.data_platform.models import CLASSIFICATIONS
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class DataGovernance:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def set_policy(
        self,
        *,
        entity_id: str,
        classification: str = "internal",
        retention_days: int = 365,
        access: list[str] | None = None,
        lifecycle: str = "active",
    ) -> dict[str, Any]:
        cls = classification.lower().strip()
        if cls not in CLASSIFICATIONS:
            raise ValidationError(f"classification must be one of {list(CLASSIFICATIONS)}")
        if not entity_id:
            raise ValidationError("entity_id required")
        pid = _id("edp_gov")
        return self.store.edp_governance.save(
            pid,
            {
                "policy_id": pid,
                "entity_id": entity_id,
                "classification": cls,
                "retention_days": int(retention_days),
                "access": access or ["owner"],
                "lifecycle": lifecycle,
                "at": _now(),
            },
        )

    def audit(
        self,
        *,
        entity_id: str,
        actor: str,
        action: str,
        detail: str = "",
    ) -> dict[str, Any]:
        if not entity_id or not actor or not action:
            raise ValidationError("entity_id, actor, and action required")
        aid = _id("edp_audit")
        return self.store.edp_audit.save(
            aid,
            {
                "audit_id": aid,
                "entity_id": entity_id,
                "actor": actor,
                "action": action,
                "detail": detail,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "policies": self.store.edp_governance.count(),
            "audit": self.store.edp_audit.count(),
            "classifications": list(CLASSIFICATIONS),
        }
