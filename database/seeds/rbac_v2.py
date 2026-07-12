# RBAC v2 default roles and permissions.

from __future__ import annotations

DEFAULT_ROLES: tuple[tuple[str, str, str], ...] = (
    ("OWNER", "Owner", "Full platform ownership"),
    ("ADMIN", "Administrator", "Platform administration"),
    ("MANAGER", "Manager", "CRM and deal management"),
    ("LAWYER", "Lawyer", "Legal module access"),
    ("DRONE_ENGINEER", "Drone Engineer", "Drone operations access"),
    ("BEAUTY_MANAGER", "Beauty Manager", "Beauty vertical management"),
    ("ACCOUNTANT", "Accountant", "Finance and ledger access"),
    ("PARTNER", "Partner", "Partner portal access"),
)

DEFAULT_PERMISSIONS: tuple[tuple[str, str], ...] = (
    ("crm.read", "Read CRM data"),
    ("crm.write", "Create and update CRM data"),
    ("users.read", "View users"),
    ("users.write", "Create and update users"),
    ("roles.manage", "Manage roles and assignments"),
    ("finance.read", "View finance accounts and transactions"),
    ("finance.write", "Create and update finance records"),
    ("ledger.read", "View ledger entries"),
    ("ledger.write", "Create and update ledger entries"),
    ("partner.read", "View partners"),
    ("partner.write", "Create and update partners"),
    ("deal.read", "View deals"),
    ("deal.write", "Create and update deals"),
    ("commission.read", "View commissions"),
    ("commission.write", "Create and update commissions"),
    ("deal.created", "Emit or subscribe to deal created events"),
    ("deal.updated", "Emit or subscribe to deal updated events"),
    ("payment.received", "Emit or subscribe to payment received events"),
    ("partner.assigned", "Emit or subscribe to partner assigned events"),
    ("commission.created", "Emit or subscribe to commission created events"),
    ("ledger.entry.created", "Emit or subscribe to ledger entry created events"),
)

ALL_PERMISSION_CODES: frozenset[str] = frozenset(code for code, _ in DEFAULT_PERMISSIONS)

DEFAULT_ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "OWNER": ALL_PERMISSION_CODES,
    "ADMIN": ALL_PERMISSION_CODES,
    "MANAGER": frozenset(
        {
            "crm.read",
            "crm.write",
            "users.read",
            "deal.read",
            "deal.write",
            "deal.created",
            "deal.updated",
            "partner.read",
            "partner.assigned",
            "commission.read",
            "commission.created",
        }
    ),
    "LAWYER": frozenset(
        {"crm.read", "deal.read", "deal.created", "deal.updated", "ledger.read", "ledger.entry.created"}
    ),
    "DRONE_ENGINEER": frozenset(
        {"crm.read", "deal.read", "deal.write", "deal.created", "deal.updated"}
    ),
    "BEAUTY_MANAGER": frozenset(
        {
            "crm.read",
            "crm.write",
            "deal.read",
            "deal.write",
            "deal.created",
            "deal.updated",
            "partner.read",
            "partner.assigned",
        }
    ),
    "ACCOUNTANT": frozenset(
        {
            "finance.read",
            "finance.write",
            "ledger.read",
            "ledger.write",
            "ledger.entry.created",
            "commission.read",
            "commission.created",
            "payment.received",
        }
    ),
    "PARTNER": frozenset(
        {"partner.read", "deal.read", "deal.created", "partner.assigned"}
    ),
}
