# Agro Marketplace role-based permissions — reuses Ecosystem Identity + Governance.

from __future__ import annotations

from applications.agro_marketplace.shared.exceptions import AuthorizationError
from applications.agro_marketplace.shared.models import AgroRole

ROLE_PERMISSIONS: dict[AgroRole, set[str]] = {
    AgroRole.FARMER: {
        "farmers:read",
        "farmers:write",
        "products:read",
        "products:write",
        "harvests:write",
        "orders:read",
        "warehouse:read",
        "warehouse:write",
        "catalog:read",
    },
    AgroRole.BUYER: {
        "buyers:read",
        "buyers:write",
        "products:read",
        "orders:read",
        "orders:write",
        "catalog:read",
        "offers:write",
    },
    AgroRole.SUPPLIER: {
        "suppliers:read",
        "suppliers:write",
        "products:read",
        "catalog:read",
        "orders:read",
    },
    AgroRole.EXPORTER: {
        "export:read",
        "export:write",
        "orders:read",
        "documents:read",
        "documents:write",
        "catalog:read",
    },
    AgroRole.LOGISTICS: {
        "logistics:read",
        "logistics:write",
        "orders:read",
        "deliveries:write",
        "warehouse:read",
    },
    AgroRole.ADMINISTRATOR: {"*"},
    AgroRole.OWNER: {"*"},
    AgroRole.AI_AGENT: {
        "catalog:read",
        "products:read",
        "orders:read",
        "analytics:read",
        "recommendations:read",
        "assistant:use",
    },
}


class PermissionService:
    """Role-based access control for Agro Marketplace roles."""

    def has_permission(self, role: AgroRole | str, permission: str) -> bool:
        agro_role = AgroRole(role) if isinstance(role, str) else role
        perms = ROLE_PERMISSIONS.get(agro_role, set())
        return "*" in perms or permission in perms

    def require(self, role: AgroRole | str, permission: str) -> None:
        if not self.has_permission(role, permission):
            raise AuthorizationError(f"Missing permission: {permission}")

    def roles(self) -> list[str]:
        return [r.value for r in AgroRole]


permission_service = PermissionService()
