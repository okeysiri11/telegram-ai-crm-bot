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

from applications.enterprise_hub.api_standardization.models import AUTH_MECHANISMS


class AuthStandard:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def policy(self) -> dict[str, Any]:
        pid = _id("eas_auth")
        record = {
            "policy_id": pid,
            "mechanisms": list(AUTH_MECHANISMS),
            "required_headers": {
                "oauth2": ["Authorization"],
                "jwt": ["Authorization"],
                "api_key": ["X-API-Key"],
                "service_token": ["X-Service-Token"],
                "rbac": ["X-Roles"],
                "multi_tenant_context": ["X-Tenant-Id"],
            },
            "rbac_roles": ["viewer", "operator", "admin", "service"],
            "built_at": _now(),
        }
        self.store.eas_auth_policies.save(pid, record)
        return record

    def validate_context(self, headers: dict[str, str] | None = None) -> dict[str, Any]:
        headers = {k.lower(): v for k, v in (headers or {}).items()}
        mechanisms_present = []
        if headers.get("authorization", "").lower().startswith("bearer "):
            mechanisms_present.append("jwt")
        if headers.get("x-api-key"):
            mechanisms_present.append("api_key")
        if headers.get("x-service-token"):
            mechanisms_present.append("service_token")
        if headers.get("x-roles"):
            mechanisms_present.append("rbac")
        if headers.get("x-tenant-id"):
            mechanisms_present.append("multi_tenant_context")
        return {
            "authenticated": bool(mechanisms_present),
            "mechanisms": mechanisms_present,
            "tenant_id": headers.get("x-tenant-id"),
        }
