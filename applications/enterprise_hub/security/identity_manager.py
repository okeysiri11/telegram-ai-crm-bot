"""Identity manager — users, service accounts, AI agents, external systems."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.security.models import IDENTITY_TYPES, ROLES
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class IdentityManager:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def find_by_subject(self, *, subject: str) -> dict[str, Any] | None:
        needle = subject.strip().lower()
        for item in self.store.isam_identities.list_all():
            if not isinstance(item, dict):
                continue
            if str(item.get("subject") or "").strip().lower() == needle:
                return item
        return None

    def register_or_get(
        self,
        *,
        subject: str,
        identity_type: str = "user",
        roles: list[str] | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        existing = self.find_by_subject(subject=subject)
        if existing is not None:
            if attributes:
                merged = dict(existing.get("attributes") or {})
                merged.update(attributes)
                existing["attributes"] = merged
                existing["at"] = _now()
                self.store.isam_identities.save(existing["identity_id"], existing)
            return existing
        return self.register(
            subject=subject,
            identity_type=identity_type,
            roles=roles,
            attributes=attributes,
        )

    def register(
        self,
        *,
        subject: str,
        identity_type: str = "user",
        roles: list[str] | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not subject:
            raise ValidationError("subject required")
        it = identity_type.lower().strip()
        if it not in IDENTITY_TYPES:
            raise ValidationError(f"identity_type must be one of {list(IDENTITY_TYPES)}")
        role_list = [r.lower() for r in (roles or ["employee"])]
        for r in role_list:
            if r not in ROLES:
                raise ValidationError(f"role must be one of {list(ROLES)}")
        # Idempotent when subject already exists (Google first login)
        existing = self.find_by_subject(subject=subject)
        if existing is not None:
            return existing
        iid = _id("isam_id")
        return self.store.isam_identities.save(
            iid,
            {
                "identity_id": iid,
                "subject": subject,
                "identity_type": it,
                "roles": role_list,
                "attributes": attributes or {},
                "status": "active",
                "email_verified": False,
                "mfa_enabled": False,
                "at": _now(),
            },
        )

    def get(self, *, identity_id: str) -> dict[str, Any]:
        item = self.store.isam_identities.get(identity_id)
        if item is None:
            raise NotFoundError(f"identity not found: {identity_id}")
        return item

    def deactivate(self, *, identity_id: str) -> dict[str, Any]:
        item = self.get(identity_id=identity_id)
        item["status"] = "deactivated"
        item["at"] = _now()
        return self.store.isam_identities.save(identity_id, item)

    def status(self) -> dict[str, Any]:
        return {
            "identities": self.store.isam_identities.count(),
            "types": list(IDENTITY_TYPES),
        }
