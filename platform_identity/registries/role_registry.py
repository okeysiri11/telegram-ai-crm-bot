# Sprint 34.2A — Canonical role registry (single source of truth).
#
# All clients (Web, Telegram, Mobile, API) MUST use these codes.
# Legacy aliases map into this registry — do not invent parallel matrices.

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CanonicalRole(str, Enum):
    OWNER = "owner"
    CEO = "ceo"
    ADMINISTRATOR = "administrator"
    MANAGER = "manager"
    EMPLOYEE = "employee"
    OPERATOR = "operator"
    PARTNER = "partner"
    DEALER = "dealer"
    CLIENT = "client"
    GUEST = "guest"


@dataclass(frozen=True)
class RoleDefinition:
    code: CanonicalRole
    label: str
    description: str
    # Maps to permission_engine / IAM legacy codes (uppercase or PlatformRole values).
    aliases: tuple[str, ...] = ()


ROLE_REGISTRY: dict[str, RoleDefinition] = {
    CanonicalRole.OWNER.value: RoleDefinition(
        code=CanonicalRole.OWNER,
        label="Owner",
        description="Full platform ownership — identical on every client",
        aliases=("OWNER", "SUPER_ADMIN", "company_owner", "owner"),
    ),
    CanonicalRole.CEO.value: RoleDefinition(
        code=CanonicalRole.CEO,
        label="CEO",
        description="Executive persona — authorization equivalent to Owner for enterprise surfaces",
        aliases=("CEO", "ceo"),
    ),
    CanonicalRole.ADMINISTRATOR.value: RoleDefinition(
        code=CanonicalRole.ADMINISTRATOR,
        label="Administrator",
        description="Platform administration",
        aliases=("ADMIN", "ADMINISTRATOR", "administrator"),
    ),
    CanonicalRole.MANAGER.value: RoleDefinition(
        code=CanonicalRole.MANAGER,
        label="Manager",
        description="Operational manager (CRM, team scope)",
        aliases=(
            "MANAGER",
            "AUTO_MANAGER",
            "AGRO_MANAGER",
            "DEALER_MANAGER",
            "manager",
        ),
    ),
    CanonicalRole.EMPLOYEE.value: RoleDefinition(
        code=CanonicalRole.EMPLOYEE,
        label="Employee",
        description="Internal staff — maps to operator-level grants when no finer role set",
        aliases=("EMPLOYEE", "employee", "role_employee"),
    ),
    CanonicalRole.OPERATOR.value: RoleDefinition(
        code=CanonicalRole.OPERATOR,
        label="Operator",
        description="Task / workflow operator",
        aliases=("OPERATOR", "operator"),
    ),
    CanonicalRole.PARTNER.value: RoleDefinition(
        code=CanonicalRole.PARTNER,
        label="Partner",
        description="External partner",
        aliases=("PARTNER", "partner"),
    ),
    CanonicalRole.DEALER.value: RoleDefinition(
        code=CanonicalRole.DEALER,
        label="Dealer",
        description="Dealer / marketplace partner",
        aliases=("DEALER", "dealer", "DEALER_MANAGER"),
    ),
    CanonicalRole.CLIENT.value: RoleDefinition(
        code=CanonicalRole.CLIENT,
        label="Client",
        description="External client / customer",
        aliases=("CLIENT", "client", "CUSTOMER", "readonly", "READ_ONLY"),
    ),
    CanonicalRole.GUEST.value: RoleDefinition(
        code=CanonicalRole.GUEST,
        label="Guest",
        description="Unauthenticated or limited public scope (Digital Citizen)",
        aliases=("GUEST", "guest", "viewer", "VIEWER"),
    ),
}


# Alias → canonical role code (lowercase).
_ALIAS_INDEX: dict[str, str] = {}
for _code, _def in ROLE_REGISTRY.items():
    _ALIAS_INDEX[_code.lower()] = _code
    for _alias in _def.aliases:
        _ALIAS_INDEX[_alias.lower()] = _code


def normalize_role(raw: str | None) -> str | None:
    """Map any legacy / client role string to a canonical role code."""
    if not raw:
        return None
    return _ALIAS_INDEX.get(str(raw).strip().lower())


def normalize_roles(raw_roles: list[str] | tuple[str, ...] | None) -> list[str]:
    """Deduped canonical role codes preserving first-seen order."""
    out: list[str] = []
    seen: set[str] = set()
    for r in raw_roles or []:
        c = normalize_role(r)
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out


def all_role_codes() -> list[str]:
    return list(ROLE_REGISTRY.keys())


def role_definition(code: str) -> RoleDefinition | None:
    canon = normalize_role(code)
    if not canon:
        return None
    return ROLE_REGISTRY.get(canon)
