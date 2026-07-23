"""Permissions engine."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


DEFAULT_ROLE_PERMS = {
    "super_admin": ["*"],
    "platform_admin": ["manage_platform", "manage_users", "view_audit"],
    "company_owner": ["manage_company", "manage_users", "view_reports"],
    "manager": ["manage_team", "approve", "view_reports"],
    "employee": ["view", "edit_own"],
    "auditor": ["view_audit", "view"],
    "ai_agent": ["execute_task", "read_context"],
    "integration_service": ["api_call", "sync"],
    "read_only": ["view"],
}


class PermissionEngine:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def grant(self, *, identity_id: str, permission: str) -> dict[str, Any]:
        if not identity_id or not permission:
            raise ValidationError("identity_id and permission required")
        pid = _id("isam_perm")
        return self.store.isam_permissions.save(
            pid,
            {
                "permission_id": pid,
                "identity_id": identity_id,
                "permission": permission,
                "at": _now(),
            },
        )

    def resolve(self, *, identity_id: str) -> dict[str, Any]:
        identity = self.store.isam_identities.get(identity_id)
        if identity is None:
            from applications.enterprise_hub.shared.exceptions import NotFoundError

            raise NotFoundError(f"identity not found: {identity_id}")
        perms: set[str] = set()
        for role in identity.get("roles") or []:
            perms.update(DEFAULT_ROLE_PERMS.get(role, []))
        for item in self.store.isam_permissions.list_all():
            if isinstance(item, dict) and item.get("identity_id") == identity_id:
                perms.add(item["permission"])
        rid = _id("isam_pres")
        return self.store.isam_permission_resolutions.save(
            rid,
            {
                "resolution_id": rid,
                "identity_id": identity_id,
                "permissions": sorted(perms),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "grants": self.store.isam_permissions.count(),
            "resolutions": self.store.isam_permission_resolutions.count(),
        }
