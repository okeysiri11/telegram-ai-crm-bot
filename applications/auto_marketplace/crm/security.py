# CRM RBAC — role-based permissions via Security Layer bridge.

from __future__ import annotations

from applications.auto_marketplace.crm.models import CRMRole

_PERMISSIONS: dict[CRMRole, set[str]] = {
    CRMRole.OWNER: {"*"},
    CRMRole.ADMINISTRATOR: {
        "crm.read", "crm.write", "crm.delete", "leads.manage", "deals.manage",
        "customers.manage", "tasks.manage", "pipeline.manage", "reports.view",
    },
    CRMRole.SALES_MANAGER: {
        "crm.read", "crm.write", "leads.manage", "deals.manage", "customers.read",
        "tasks.manage", "pipeline.manage", "reports.view",
    },
    CRMRole.SALES_AGENT: {
        "crm.read", "crm.write", "leads.read", "leads.write", "deals.read", "deals.write",
        "customers.read", "customers.write", "tasks.read", "tasks.write",
        "pipeline.read", "reports.view",
    },
    CRMRole.DEALER: {"crm.read", "leads.read", "deals.read", "customers.read"},
    CRMRole.CUSTOMER: {"crm.read.self", "deals.read.self"},
    CRMRole.AI_AGENT: {"crm.read", "leads.read", "leads.score", "deals.predict", "tasks.suggest"},
}


class CRMSecurity:
    def authorize(self, role: CRMRole | str, permission: str) -> bool:
        if isinstance(role, str):
            try:
                role = CRMRole(role)
            except ValueError:
                return False
        perms = _PERMISSIONS.get(role, set())
        if "*" in perms:
            return True
        return permission in perms

    async def authorize_principal(self, principal: dict | None, permission: str) -> bool:
        if principal is None:
            return permission.endswith(".read")
        role = principal.get("role", CRMRole.SALES_AGENT.value)
        return self.authorize(role, permission)

    def require(self, role: CRMRole | str, permission: str) -> None:
        from applications.auto_marketplace.shared.exceptions import AuthorizationError

        if not self.authorize(role, permission):
            raise AuthorizationError(f"Permission denied: {permission}")


crm_security = CRMSecurity()
