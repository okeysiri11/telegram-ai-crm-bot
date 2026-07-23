"""API key management."""

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


class APIKeyManager:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def create(self, *, identity_id: str, name: str = "default") -> dict[str, Any]:
        if not identity_id:
            raise ValidationError("identity_id required")
        if self.store.isam_identities.get(identity_id) is None:
            raise NotFoundError(f"identity not found: {identity_id}")
        kid = _id("isam_key")
        return self.store.isam_api_keys.save(
            kid,
            {
                "key_id": kid,
                "identity_id": identity_id,
                "name": name or "default",
                "key": f"eip_{uuid.uuid4().hex}",
                "status": "active",
                "at": _now(),
            },
        )

    def revoke(self, *, key_id: str) -> dict[str, Any]:
        key = self.store.isam_api_keys.get(key_id)
        if key is None:
            raise NotFoundError(f"api key not found: {key_id}")
        key["status"] = "revoked"
        key["at"] = _now()
        return self.store.isam_api_keys.save(key_id, key)

    def status(self) -> dict[str, Any]:
        return {"keys": self.store.isam_api_keys.count()}
