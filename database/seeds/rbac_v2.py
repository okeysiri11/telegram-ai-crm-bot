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
            "partner.read",
            "commission.read",
        }
    ),
    "LAWYER": frozenset({"crm.read", "deal.read", "ledger.read"}),
    "DRONE_ENGINEER": frozenset({"crm.read", "deal.read", "deal.write"}),
    "BEAUTY_MANAGER": frozenset(
        {"crm.read", "crm.write", "deal.read", "deal.write", "partner.read"}
    ),
    "ACCOUNTANT": frozenset(
        {
            "finance.read",
            "finance.write",
            "ledger.read",
            "ledger.write",
            "commission.read",
        }
    ),
    "PARTNER": frozenset({"partner.read", "deal.read"}),
}
