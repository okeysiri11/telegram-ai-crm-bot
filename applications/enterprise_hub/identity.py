"""Enterprise identity — unified identity, org/user/role mapping, permission sync."""

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


class EnterpriseIdentity:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def register_identity(
        self, *, subject: str, identity_type: str = "user", platforms: list[str] | None = None
    ) -> dict[str, Any]:
        if not subject:
            raise ValidationError("subject required")
        iid = _id("hub_id")
        return self.store.identities.save(
            iid,
            {
                "identity_id": iid,
                "subject": subject,
                "identity_type": identity_type,
                "platforms": platforms or [],
                "at": _now(),
            },
        )

    def map_organization(
        self, *, hub_org_id: str, platform: str, external_org_id: str
    ) -> dict[str, Any]:
        if not hub_org_id or not platform or not external_org_id:
            raise ValidationError("hub_org_id, platform, and external_org_id required")
        mid = _id("hub_omap")
        return self.store.org_mappings.save(
            mid,
            {
                "mapping_id": mid,
                "hub_org_id": hub_org_id,
                "platform": platform.lower(),
                "external_org_id": external_org_id,
                "at": _now(),
            },
        )

    def register_user(
        self, *, username: str, identity_id: str = "", platforms: list[str] | None = None
    ) -> dict[str, Any]:
        if not username:
            raise ValidationError("username required")
        uid = _id("hub_usr")
        return self.store.users.save(
            uid,
            {
                "user_id": uid,
                "username": username,
                "identity_id": identity_id,
                "platforms": platforms or [],
                "at": _now(),
            },
        )

    def map_role(
        self, *, hub_role: str, platform: str, platform_role: str
    ) -> dict[str, Any]:
        if not hub_role or not platform or not platform_role:
            raise ValidationError("hub_role, platform, and platform_role required")
        rid = _id("hub_rmap")
        return self.store.role_mappings.save(
            rid,
            {
                "mapping_id": rid,
                "hub_role": hub_role,
                "platform": platform.lower(),
                "platform_role": platform_role,
                "at": _now(),
            },
        )

    def sync_permissions(
        self, *, platform: str, permissions: list[str] | None = None
    ) -> dict[str, Any]:
        if not platform:
            raise ValidationError("platform required")
        sid = _id("hub_psync")
        perms = permissions or []
        return self.store.permission_syncs.save(
            sid,
            {
                "sync_id": sid,
                "platform": platform.lower(),
                "permissions": perms,
                "count": len(perms),
                "status": "synced",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "identities": self.store.identities.count(),
            "org_mappings": self.store.org_mappings.count(),
            "users": self.store.users.count(),
            "role_mappings": self.store.role_mappings.count(),
            "permission_syncs": self.store.permission_syncs.count(),
        }
