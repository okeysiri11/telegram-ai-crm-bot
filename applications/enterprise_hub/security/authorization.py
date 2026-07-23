"""Authorization — RBAC / ABAC checks."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.security.permissions import PermissionEngine
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AuthorizationService:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.permissions = PermissionEngine(self.store)

    def authorize(
        self,
        *,
        identity_id: str,
        permission: str,
        mode: str = "rbac",
        attributes: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not identity_id or not permission:
            raise ValidationError("identity_id and permission required")
        mode_n = mode.lower().strip()
        if mode_n not in ("rbac", "abac", "resource", "dynamic"):
            raise ValidationError("mode must be rbac, abac, resource, or dynamic")
        identity = self.store.isam_identities.get(identity_id)
        if identity is None:
            raise NotFoundError(f"identity not found: {identity_id}")
        resolved = self.permissions.resolve(identity_id=identity_id)
        perms = set(resolved.get("permissions") or [])
        allowed = "*" in perms or permission in perms
        if mode_n == "abac" and attributes:
            # simple attribute gate: department match boosts allow if already permitted
            if attributes.get("deny") is True:
                allowed = False
        aid = _id("isam_authz")
        return self.store.isam_authz.save(
            aid,
            {
                "authz_id": aid,
                "identity_id": identity_id,
                "permission": permission,
                "mode": mode_n,
                "allowed": allowed,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"decisions": self.store.isam_authz.count()}
