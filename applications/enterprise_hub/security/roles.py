"""Roles registry."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.security.models import ROLES
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class RoleRegistry:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def assign(self, *, identity_id: str, role: str) -> dict[str, Any]:
        r = role.lower().strip()
        if r not in ROLES:
            raise ValidationError(f"role must be one of {list(ROLES)}")
        identity = self.store.isam_identities.get(identity_id)
        if identity is None:
            from applications.enterprise_hub.shared.exceptions import NotFoundError

            raise NotFoundError(f"identity not found: {identity_id}")
        roles = list(identity.get("roles") or [])
        if r not in roles:
            roles.append(r)
        identity["roles"] = roles
        identity["at"] = _now()
        self.store.isam_identities.save(identity_id, identity)
        rid = _id("isam_role")
        return self.store.isam_role_assigns.save(
            rid,
            {
                "assignment_id": rid,
                "identity_id": identity_id,
                "role": r,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"assignments": self.store.isam_role_assigns.count(), "roles": list(ROLES)}
