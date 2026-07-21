# Port ERP RBAC — foundation roles.

from __future__ import annotations

from applications.port_erp.shared.exceptions import AuthorizationError
from applications.port_erp.shared.models import PortRole

ROLE_PERMISSIONS: dict[PortRole, set[str]] = {
    PortRole.PORT_DIRECTOR: {"*"},
    PortRole.ADMINISTRATOR: {"*"},
    PortRole.AI_EXECUTIVE: {
        "ports:read",
        "terminals:read",
        "operations:read",
        "analytics:read",
        "assistant:use",
    },
    PortRole.TERMINAL_MANAGER: {
        "terminals:read",
        "terminals:write",
        "berths:read",
        "berths:write",
        "containers:read",
        "operations:read",
        "operations:write",
        "gates:write",
    },
    PortRole.DISPATCHER: {
        "vessels:read",
        "vessels:write",
        "berths:read",
        "berths:write",
        "operations:read",
        "operations:write",
    },
    PortRole.WAREHOUSE_MANAGER: {
        "cargo:read",
        "cargo:write",
        "warehouses:read",
        "warehouses:write",
        "containers:read",
    },
    PortRole.CONTAINER_OPERATOR: {
        "containers:read",
        "containers:write",
        "operations:read",
    },
    PortRole.CRANE_OPERATOR: {
        "containers:read",
        "cargo:read",
        "operations:read",
        "operations:write",
    },
    PortRole.FORWARDER: {
        "cargo:read",
        "containers:read",
        "customers:read",
        "documents:read",
        "documents:write",
    },
    PortRole.SHIPPING_LINE: {
        "vessels:read",
        "voyages:read",
        "containers:read",
        "companies:read",
    },
    PortRole.BROKER: {
        "cargo:read",
        "documents:read",
        "documents:write",
        "customers:read",
    },
    PortRole.CUSTOMER: {
        "cargo:read",
        "containers:read",
        "documents:read",
        "billing:read",
    },
}


class PermissionService:
    def has_permission(self, role: PortRole | str, permission: str) -> bool:
        port_role = PortRole(role) if isinstance(role, str) else role
        perms = ROLE_PERMISSIONS.get(port_role, set())
        return "*" in perms or permission in perms

    def require(self, role: PortRole | str, permission: str) -> None:
        if not self.has_permission(role, permission):
            raise AuthorizationError(f"Missing permission: {permission}")

    def roles(self) -> list[str]:
        return [r.value for r in PortRole]


permission_service = PermissionService()
