"""Integration security — OAuth2, JWT, API keys, certs, vault, rotation."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.integrations.models import AUTH_METHODS
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class IntegrationSecurity:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def configure(
        self,
        *,
        integration_id: str,
        method: str,
        secret_ref: str = "",
    ) -> dict[str, Any]:
        m = method.lower().strip()
        if m not in AUTH_METHODS:
            raise ValidationError(f"method must be one of {list(AUTH_METHODS)}")
        if not integration_id:
            raise ValidationError("integration_id required")
        sid = _id("eip_sec")
        return self.store.eip_security.save(
            sid,
            {
                "security_id": sid,
                "integration_id": integration_id,
                "method": m,
                "secret_ref": secret_ref or f"vault://{integration_id}",
                "rotated": False,
                "at": _now(),
            },
        )

    def rotate_token(self, *, security_id: str) -> dict[str, Any]:
        item = self.store.eip_security.get(security_id)
        if item is None:
            from applications.enterprise_hub.shared.exceptions import NotFoundError

            raise NotFoundError(f"security config not found: {security_id}")
        item["rotated"] = True
        item["at"] = _now()
        return self.store.eip_security.save(security_id, item)

    def status(self) -> dict[str, Any]:
        return {"configs": self.store.eip_security.count(), "methods": list(AUTH_METHODS)}
