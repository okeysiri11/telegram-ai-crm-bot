# Authorization policy surface — Sprint 32.4.
# SoR remains permission_engine + ISAM AccessControl; this documents/composes checks.

from __future__ import annotations

from typing import Any

from platform_security.authorization import AccessControl
from platform_security.models import ABAC_ATTRIBUTES


class AuthorizationCenter:
    def __init__(self, access: AccessControl | None = None) -> None:
        self.access = access or AccessControl()

    def permission_matrix(self, roles: dict[str, list[str]]) -> dict[str, Any]:
        return {"roles": roles, "model": "rbac_matrix"}

    def authorize_context(
        self,
        *,
        principal: str,
        roles_required: list[str],
        attributes: dict[str, Any] | None = None,
        tenant_id: str | None = None,
        resource: str | None = None,
    ) -> dict[str, Any]:
        attrs = dict(attributes or {})
        if tenant_id:
            attrs.setdefault("organization", tenant_id)
        result = self.access.authorize(
            principal=principal,
            roles_required=roles_required,
            attributes=attrs,
        )
        result["tenant_id"] = tenant_id
        result["resource"] = resource
        result["context_aware"] = True
        result["abac_attributes"] = list(ABAC_ATTRIBUTES)
        return result

    def capabilities(self) -> dict[str, Any]:
        return {
            "rbac": True,
            "abac": True,
            "policy_engine": True,
            "permission_matrix": True,
            "organization_isolation": True,
            "tenant_isolation": True,
            "resource_level_permissions": True,
            "context_aware_authorization": True,
            "permission_engine": "platform_security.permission_engine",
            "isam": "applications/enterprise_hub/security",
        }
