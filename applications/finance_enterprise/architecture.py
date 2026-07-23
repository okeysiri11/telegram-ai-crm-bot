"""Financial architecture — event bus, audit trail, permissions, configuration."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.finance_enterprise.config import DEFAULT_CONFIG
from applications.finance_enterprise.shared.exceptions import ValidationError
from applications.finance_enterprise.shared.store import FinanceEnterpriseStore, finance_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class FinancialArchitecture:
    def __init__(self, store: FinanceEnterpriseStore | None = None) -> None:
        self.store = store or finance_enterprise_store
        self.roles = list(DEFAULT_CONFIG.finance_roles)

    def publish_event(self, *, event_type: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if not event_type:
            raise ValidationError("event_type required")
        eid = _id("fe_evt")
        return self.store.events.save(
            eid,
            {
                "event_id": eid,
                "event_type": event_type,
                "payload": payload or {},
                "at": _now(),
            },
        )

    def audit(
        self, *, action: str, actor: str = "system", resource: str = "", detail: str = ""
    ) -> dict[str, Any]:
        if not action:
            raise ValidationError("action required")
        aid = _id("fe_aud")
        return self.store.audit_trail.save(
            aid,
            {
                "audit_id": aid,
                "action": action,
                "actor": actor,
                "resource": resource,
                "detail": detail,
                "at": _now(),
            },
        )

    def grant_permission(self, *, role: str, permission: str, resource: str = "*") -> dict[str, Any]:
        if role not in self.roles:
            raise ValidationError(f"role must be one of {self.roles}")
        if not permission:
            raise ValidationError("permission required")
        pid = _id("fe_perm")
        return self.store.permissions.save(
            pid,
            {
                "permission_id": pid,
                "role": role,
                "permission": permission,
                "resource": resource,
                "at": _now(),
            },
        )

    def set_config(self, *, key: str, value: Any) -> dict[str, Any]:
        if not key:
            raise ValidationError("key required")
        return self.store.financial_config.save(
            key,
            {
                "config_id": _id("fe_cfg"),
                "key": key,
                "value": value,
                "updated_at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "events": self.store.events.count(),
            "audit_entries": self.store.audit_trail.count(),
            "permissions": self.store.permissions.count(),
            "config_keys": self.store.financial_config.count(),
            "roles": self.roles,
        }
