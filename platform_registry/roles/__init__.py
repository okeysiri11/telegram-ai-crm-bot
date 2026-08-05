"""Platform role catalog — labels for clients; codes from Identity Core."""

from __future__ import annotations

from dataclasses import dataclass

from platform_identity.registries.role_registry import ROLE_REGISTRY, CanonicalRole, normalize_role


@dataclass(frozen=True)
class PlatformRoleView:
    code: str
    title: str
    description: str
    aliases: tuple[str, ...]


# Product-facing titles (permissions still via Identity Core only).
PLATFORM_ROLE_TITLES: dict[str, str] = {
    "owner": "Platform Owner",
    "ceo": "Company Owner",
    "administrator": "Administrator",
    "manager": "Manager",
    "operator": "Operator",
    "employee": "Employee",
    "partner": "Partner",
    "dealer": "Dealer",
    "client": "Client",
    "guest": "Guest",
}


def all_platform_roles() -> list[PlatformRoleView]:
    out: list[PlatformRoleView] = []
    for code, d in ROLE_REGISTRY.items():
        out.append(
            PlatformRoleView(
                code=code,
                title=PLATFORM_ROLE_TITLES.get(code, d.label),
                description=d.description,
                aliases=d.aliases,
            )
        )
    return out


def role_title(code: str | None) -> str | None:
    c = normalize_role(code)
    if not c:
        return None
    return PLATFORM_ROLE_TITLES.get(c, ROLE_REGISTRY[c].label)


__all__ = [
    "CanonicalRole",
    "PLATFORM_ROLE_TITLES",
    "PlatformRoleView",
    "all_platform_roles",
    "normalize_role",
    "role_title",
]
