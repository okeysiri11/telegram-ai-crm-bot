# Canonical CRM roles, verticals, and manager lead statuses.

from __future__ import annotations

from enum import Enum


class SystemRole(str, Enum):
    """Top-level CRM / platform roles for vertical routing."""

    SUPER_ADMIN = "SUPER_ADMIN"
    AUTO_MANAGER = "AUTO_MANAGER"
    AGRO_MANAGER = "AGRO_MANAGER"
    CLIENT = "CLIENT"


class Vertical(str, Enum):
    """Business verticals used for lead routing and manager subscriptions."""

    AUTO = "auto"
    AGRO = "agro"
    REALTY = "realty"
    LOGISTICS = "logistics"


class ManagerLeadStatus(str, Enum):
    """Manager-facing request lifecycle (CRM dashboard)."""

    NEW = "NEW"
    TAKEN = "TAKEN"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING_CLIENT = "WAITING_CLIENT"
    DEAL = "DEAL"
    CLOSED = "CLOSED"
    REJECTED = "REJECTED"


SYSTEM_ROLE_CODES = frozenset(role.value for role in SystemRole)
VERTICAL_CODES = frozenset(v.value for v in Vertical)
MANAGER_LEAD_STATUSES = frozenset(s.value for s in ManagerLeadStatus)

# Role → default vertical subscriptions
ROLE_DEFAULT_VERTICALS: dict[str, tuple[str, ...]] = {
    SystemRole.SUPER_ADMIN.value: (
        Vertical.AUTO.value,
        Vertical.AGRO.value,
        Vertical.REALTY.value,
        Vertical.LOGISTICS.value,
    ),
    SystemRole.AUTO_MANAGER.value: (Vertical.AUTO.value,),
    SystemRole.AGRO_MANAGER.value: (Vertical.AGRO.value,),
    SystemRole.CLIENT.value: (),
}

# Access matrix (high-level)
ROLE_ACCESS: dict[str, frozenset[str]] = {
    SystemRole.SUPER_ADMIN.value: frozenset({
        "admin_panel",
        "all_verticals",
        "all_leads",
        "analytics",
        "finance",
        "users",
        "settings",
        "ai_control",
        "reassign_leads",
    }),
    SystemRole.AUTO_MANAGER.value: frozenset({
        "manager_crm",
        "auto_leads",
        "take_lead",
        "update_status",
        "message_client",
        "close_lead",
    }),
    SystemRole.AGRO_MANAGER.value: frozenset({
        "manager_crm",
        "agro_leads",
        "take_lead",
        "update_status",
        "message_client",
        "close_lead",
    }),
    SystemRole.CLIENT.value: frozenset({
        "client_vertical_menu",
        "create_request",
    }),
}

# Map legacy / permission-engine codes onto SystemRole where possible
LEGACY_ROLE_ALIASES: dict[str, str] = {
    "OWNER": SystemRole.SUPER_ADMIN.value,
    "ADMIN": SystemRole.SUPER_ADMIN.value,
    "SUPER_MANAGER": SystemRole.SUPER_ADMIN.value,
    "MANAGER": SystemRole.AUTO_MANAGER.value,
    "DEALER_MANAGER": SystemRole.AUTO_MANAGER.value,
    "AGRO_MANAGER": SystemRole.AGRO_MANAGER.value,
    "AUTO_MANAGER": SystemRole.AUTO_MANAGER.value,
    "CLIENT": SystemRole.CLIENT.value,
}


def normalize_vertical(value: str | None) -> str | None:
    if not value:
        return None
    key = value.strip().lower()
    if key in VERTICAL_CODES:
        return key
    # Common entry-link aliases
    aliases = {
        "auto_client": Vertical.AUTO.value,
        "auto_dealer": Vertical.AUTO.value,
        "automotive": Vertical.AUTO.value,
        "agriculture": Vertical.AGRO.value,
        "agro_trading": Vertical.AGRO.value,
    }
    return aliases.get(key)


def role_has_access(role: str | SystemRole, capability: str) -> bool:
    code = role.value if isinstance(role, SystemRole) else str(role)
    return capability in ROLE_ACCESS.get(code, frozenset())
