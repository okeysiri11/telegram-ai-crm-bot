# Permission Engine default roles and permissions.

from __future__ import annotations

DEFAULT_ROLES: tuple[tuple[str, str, str], ...] = (
    ("OWNER", "Owner", "Full platform access"),
    ("ADMIN", "Administrator", "Administrative access"),
    ("MANAGER", "Manager", "Deal and team management"),
    ("ACCOUNTANT", "Accountant", "Finance and ledger access"),
    ("LAWYER", "Lawyer", "Legal and audit read access"),
    ("PARTNER", "Partner", "Partner portal access"),
    ("OPERATOR", "Operator", "Operational deal processing"),
    ("VIEWER", "Viewer", "Read-only access"),
)

DEFAULT_PERMISSIONS: tuple[tuple[str, str], ...] = (
    ("VIEW_DEALS", "View deals"),
    ("CREATE_DEALS", "Create deals"),
    ("EDIT_DEALS", "Edit deals"),
    ("DELETE_DEALS", "Delete deals"),
    ("VIEW_LEDGER", "View ledger"),
    ("EDIT_LEDGER", "Edit ledger"),
    ("VIEW_COMMISSIONS", "View commissions"),
    ("PAY_COMMISSIONS", "Pay commissions"),
    ("VIEW_USERS", "View users"),
    ("CREATE_USERS", "Create users"),
    ("EDIT_USERS", "Edit users"),
    ("DELETE_USERS", "Delete users"),
    ("VIEW_AUDIT", "View audit logs"),
    ("EXPORT_AUDIT", "Export audit logs"),
    ("VIEW_REPORTS", "View reports"),
    ("EXPORT_REPORTS", "Export reports"),
    ("MANAGE_SETTINGS", "Manage platform settings"),
)

ALL_PERMISSION_CODES: frozenset[str] = frozenset(code for code, _ in DEFAULT_PERMISSIONS)

DEFAULT_ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "OWNER": ALL_PERMISSION_CODES,
    "ADMIN": ALL_PERMISSION_CODES,
    "MANAGER": frozenset(
        {
            "VIEW_DEALS",
            "CREATE_DEALS",
            "EDIT_DEALS",
            "VIEW_COMMISSIONS",
            "VIEW_REPORTS",
        }
    ),
    "ACCOUNTANT": frozenset(
        {
            "VIEW_DEALS",
            "VIEW_LEDGER",
            "EDIT_LEDGER",
            "VIEW_COMMISSIONS",
            "PAY_COMMISSIONS",
            "VIEW_REPORTS",
            "EXPORT_REPORTS",
        }
    ),
    "LAWYER": frozenset({"VIEW_DEALS", "VIEW_AUDIT", "EXPORT_AUDIT"}),
    "PARTNER": frozenset({"VIEW_DEALS", "VIEW_COMMISSIONS"}),
    "OPERATOR": frozenset({"VIEW_DEALS", "CREATE_DEALS", "EDIT_DEALS"}),
    "VIEWER": frozenset({"VIEW_DEALS", "VIEW_REPORTS"}),
}
