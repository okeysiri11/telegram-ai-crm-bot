# RBAC v2 — roles, permissions, inheritance, and role templates.

from __future__ import annotations

RBAC_V2_ROLES: tuple[tuple[str, str, str], ...] = (
    ("OWNER", "Owner", "Full platform ownership"),
    ("SUPER_MANAGER", "Super Manager", "Cross-vertical platform management"),
    ("AUTO_OWNER", "Auto Owner", "Automotive tenant owner"),
    ("AUTO_MANAGER", "Auto Manager", "Automotive operations manager"),
    ("AUTO_OPERATOR", "Auto Operator", "Automotive day-to-day operator"),
    ("FINANCE_MANAGER", "Finance Manager", "Finance and treasury access"),
    ("LAW_MANAGER", "Law Manager", "Legal module access"),
    ("AGRO_MANAGER", "Agro Manager", "Agro trading module access"),
    ("DRONE_MANAGER", "Drone Manager", "Drone operations access"),
    ("CLIENT_OWNER", "Client Owner", "Client tenant owner"),
    ("CLIENT_MANAGER", "Client Manager", "Client tenant manager"),
)

RBAC_V2_PERMISSIONS: tuple[tuple[str, str, str | None, str], ...] = (
    # module access
    ("auto.module", "module", None, "Automotive module access"),
    ("agro.module", "module", None, "Agro module access"),
    ("finance.module", "module", None, "Finance module access"),
    ("legal.module", "module", None, "Legal module access"),
    ("drone.module", "module", None, "Drone module access"),
    ("billing.module", "module", None, "Billing module access"),
    ("analytics.module", "module", None, "Analytics module access"),
    # entity access
    ("auto.car.read", "entity", "auto.module", "View automotive inventory"),
    ("auto.car.write", "entity", "auto.car.read", "Manage automotive inventory"),
    ("auto.lead.read", "entity", "auto.module", "View automotive leads"),
    ("auto.lead.write", "entity", "auto.lead.read", "Manage automotive leads"),
    ("deal.read", "entity", "finance.module", "View deals"),
    ("deal.write", "entity", "deal.read", "Manage deals"),
    # tenant access
    ("tenant.read", "tenant", None, "View tenant metadata"),
    ("tenant.write", "tenant", "tenant.read", "Update tenant settings"),
    ("tenant.admin", "tenant", "tenant.write", "Administer tenant members"),
    ("tenant.isolated", "tenant", "tenant.read", "Enforce tenant data isolation"),
    # billing access
    ("billing.view", "billing", "billing.module", "View billing and plans"),
    ("billing.pay", "billing", "billing.view", "Submit payments"),
    ("billing.approve", "billing", "billing.view", "Approve payments"),
    ("billing.manage", "billing", "billing.approve", "Manage subscriptions"),
    # analytics access
    ("analytics.view", "analytics", "analytics.module", "View analytics dashboards"),
    ("analytics.export", "analytics", "analytics.view", "Export analytics data"),
)

ALL_RBAC_V2_PERMISSION_CODES: frozenset[str] = frozenset(p[0] for p in RBAC_V2_PERMISSIONS)

RBAC_V2_ROLE_INHERITANCE: dict[str, frozenset[str]] = {
    "AUTO_OPERATOR": frozenset(),
    "AUTO_MANAGER": frozenset({"AUTO_OPERATOR"}),
    "AUTO_OWNER": frozenset({"AUTO_MANAGER"}),
    "CLIENT_MANAGER": frozenset({"CLIENT_OWNER"}),
    "FINANCE_MANAGER": frozenset(),
    "LAW_MANAGER": frozenset(),
    "AGRO_MANAGER": frozenset(),
    "DRONE_MANAGER": frozenset(),
    "SUPER_MANAGER": frozenset(
        {"AUTO_OWNER", "FINANCE_MANAGER", "LAW_MANAGER", "AGRO_MANAGER", "DRONE_MANAGER"}
    ),
    "OWNER": frozenset({"SUPER_MANAGER"}),
    "CLIENT_OWNER": frozenset(),
}

RBAC_V2_ROLE_TEMPLATES: tuple[tuple[str, str, str, tuple[str, ...], tuple[str, ...]], ...] = (
    (
        "platform_admin",
        "Platform Admin",
        "Full platform administration template",
        ("OWNER", "SUPER_MANAGER"),
        ALL_RBAC_V2_PERMISSION_CODES,
    ),
    (
        "automotive_tenant",
        "Automotive Tenant",
        "Automotive dealership tenant template",
        ("AUTO_OWNER", "AUTO_MANAGER", "AUTO_OPERATOR"),
        (
            "auto.module",
            "auto.car.read",
            "auto.car.write",
            "auto.lead.read",
            "auto.lead.write",
            "tenant.read",
            "tenant.write",
            "tenant.isolated",
            "billing.view",
            "billing.pay",
            "analytics.view",
        ),
    ),
    (
        "client_tenant",
        "Client Tenant",
        "External client tenant template",
        ("CLIENT_OWNER", "CLIENT_MANAGER"),
        (
            "auto.module",
            "auto.car.read",
            "auto.lead.read",
            "tenant.read",
            "tenant.isolated",
            "billing.view",
            "billing.pay",
            "analytics.view",
        ),
    ),
)

RBAC_V2_DIRECT_ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "OWNER": ALL_RBAC_V2_PERMISSION_CODES,
    "SUPER_MANAGER": frozenset(
        {
            "auto.module",
            "agro.module",
            "finance.module",
            "legal.module",
            "drone.module",
            "billing.module",
            "analytics.module",
            "auto.car.read",
            "auto.car.write",
            "auto.lead.read",
            "auto.lead.write",
            "deal.read",
            "deal.write",
            "tenant.read",
            "tenant.write",
            "tenant.admin",
            "tenant.isolated",
            "billing.view",
            "billing.approve",
            "billing.manage",
            "analytics.view",
            "analytics.export",
        }
    ),
    "AUTO_OWNER": frozenset(
        {
            "auto.module",
            "auto.car.read",
            "auto.car.write",
            "auto.lead.read",
            "auto.lead.write",
            "tenant.read",
            "tenant.write",
            "tenant.admin",
            "tenant.isolated",
            "billing.view",
            "billing.manage",
            "analytics.view",
            "analytics.export",
        }
    ),
    "AUTO_MANAGER": frozenset(
        {
            "auto.module",
            "auto.car.read",
            "auto.car.write",
            "auto.lead.read",
            "auto.lead.write",
            "tenant.read",
            "tenant.isolated",
            "billing.view",
            "analytics.view",
        }
    ),
    "AUTO_OPERATOR": frozenset(
        {
            "auto.module",
            "auto.car.read",
            "auto.car.write",
            "auto.lead.read",
            "tenant.read",
            "tenant.isolated",
            "analytics.view",
        }
    ),
    "FINANCE_MANAGER": frozenset(
        {
            "finance.module",
            "deal.read",
            "deal.write",
            "billing.module",
            "billing.view",
            "billing.approve",
            "analytics.module",
            "analytics.view",
            "analytics.export",
            "tenant.read",
        }
    ),
    "LAW_MANAGER": frozenset(
        {"legal.module", "deal.read", "tenant.read", "analytics.view"}
    ),
    "AGRO_MANAGER": frozenset(
        {"agro.module", "deal.read", "deal.write", "tenant.read", "analytics.view"}
    ),
    "DRONE_MANAGER": frozenset(
        {"drone.module", "tenant.read", "analytics.view"}
    ),
    "CLIENT_OWNER": frozenset(
        {
            "auto.module",
            "auto.car.read",
            "auto.lead.read",
            "tenant.read",
            "tenant.write",
            "tenant.isolated",
            "billing.module",
            "billing.view",
            "billing.pay",
            "analytics.view",
        }
    ),
    "CLIENT_MANAGER": frozenset(
        {
            "auto.module",
            "auto.car.read",
            "auto.lead.read",
            "tenant.read",
            "tenant.isolated",
            "billing.view",
            "analytics.view",
        }
    ),
}

# Backward-compatible exports for existing rbac_repository seed
DEFAULT_ROLES = RBAC_V2_ROLES
DEFAULT_PERMISSIONS = tuple((code, desc) for code, _, _, desc in RBAC_V2_PERMISSIONS)
ALL_PERMISSION_CODES = ALL_RBAC_V2_PERMISSION_CODES
DEFAULT_ROLE_PERMISSIONS = RBAC_V2_DIRECT_ROLE_PERMISSIONS
