# Portal RBAC — customer, dealer, partner, admin, owner, AI agent.

from __future__ import annotations

from applications.auto_marketplace.authentication.models import PortalRole

_PERMISSIONS: dict[PortalRole, set[str]] = {
    PortalRole.OWNER: {"*"},
    PortalRole.ADMINISTRATOR: {
        "portal.read", "portal.write", "customer.manage", "dealer.manage", "partner.manage",
    },
    PortalRole.CUSTOMER: {
        "portal.read", "profile.read", "profile.write", "favorites.manage", "garage.manage",
        "search.read", "search.smart", "bookings.create", "offers.create", "history.read",
        "recommendations.read", "assistant.chat",
    },
    PortalRole.DEALER: {
        "portal.read", "dealer.dashboard", "inventory.manage", "leads.manage", "sales.read",
        "analytics.read", "finance.read", "documents.read",
    },
    PortalRole.PARTNER: {
        "portal.read", "partner.integrate", "partner.webhook", "partner.read",
    },
    PortalRole.AI_AGENT: {
        "portal.read", "search.smart", "recommendations.read", "assistant.chat", "offers.generate",
    },
}


class PortalSecurity:
    def authorize(self, role: PortalRole | str, permission: str) -> bool:
        if isinstance(role, str):
            try:
                role = PortalRole(role)
            except ValueError:
                return False
        perms = _PERMISSIONS.get(role, set())
        if "*" in perms:
            return True
        return permission in perms

    def require(self, role: PortalRole | str, permission: str) -> None:
        from applications.auto_marketplace.shared.exceptions import AuthorizationError

        if not self.authorize(role, permission):
            raise AuthorizationError(f"Permission denied: {permission}")


portal_security = PortalSecurity()
