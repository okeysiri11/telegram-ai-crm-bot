"""Platform permission vocabulary — extends Identity Core without a second engine."""

from __future__ import annotations

from dataclasses import dataclass

from platform_identity.registries.permission_registry import (
    PERMISSION_REGISTRY as IDENTITY_PERMISSIONS,
    ROLE_PERMISSION_DEFAULTS,
    defaults_for_roles,
    expand_permissions,
    normalize_permission,
)


@dataclass(frozen=True)
class PermissionDef:
    code: str
    description: str
    aliases: tuple[str, ...] = ()


# Additional platform-facing permissions (aliases merge into identity normalize where possible).
PLATFORM_PERMISSIONS: dict[str, PermissionDef] = {
    **{
        code: PermissionDef(code=code, description=d.description, aliases=d.aliases)
        for code, d in IDENTITY_PERMISSIONS.items()
    },
    "calendar.read": PermissionDef("calendar.read", "Read calendar"),
    "calendar.write": PermissionDef("calendar.write", "Write calendar"),
    "tasks.read": PermissionDef("tasks.read", "Read tasks"),
    "tasks.write": PermissionDef("tasks.write", "Write tasks"),
    "analytics.read": PermissionDef("analytics.read", "Read analytics", ("analytics.view",)),
    "analytics.export": PermissionDef("analytics.export", "Export analytics"),
    "files.upload": PermissionDef("files.upload", "Upload files", ("documents.manage",)),
    "files.delete": PermissionDef("files.delete", "Delete files"),
    "studio.generate": PermissionDef("studio.generate", "Generate in AI Studio", ("ai.use",)),
    "studio.publish": PermissionDef("studio.publish", "Publish studio output"),
    "agent.execute": PermissionDef("agent.execute", "Execute AI agents", ("ai.use",)),
    "agent.train": PermissionDef("agent.train", "Train / configure agents"),
    "admin.manage": PermissionDef("admin.manage", "Administer platform", ("owner.full", "admin.access")),
    "owner.full_access": PermissionDef(
        "owner.full_access",
        "Full owner access",
        ("owner.full", "admin.access"),
    ),
}


# Extend defaults for richer module checks
_EXTENDED_DEFAULTS: dict[str, tuple[str, ...]] = {
    "owner": tuple(PLATFORM_PERMISSIONS.keys()),
    "ceo": tuple(PLATFORM_PERMISSIONS.keys()),
    "administrator": (
        "crm.read",
        "crm.write",
        "erp.read",
        "erp.write",
        "calendar.read",
        "calendar.write",
        "tasks.read",
        "tasks.write",
        "analytics.read",
        "analytics.export",
        "files.upload",
        "knowledge.read",
        "knowledge.write",
        "ai.use",
        "studio.generate",
        "agent.execute",
        "admin.manage",
        "automation.run",
    ),
    "manager": (
        "crm.read",
        "crm.write",
        "erp.read",
        "calendar.read",
        "calendar.write",
        "tasks.read",
        "tasks.write",
        "analytics.read",
        "files.upload",
        "knowledge.read",
        "ai.use",
        "agent.execute",
    ),
    "employee": (
        "crm.read",
        "calendar.read",
        "tasks.read",
        "tasks.write",
        "knowledge.read",
        "ai.use",
        "analytics.read",
    ),
    "operator": (
        "crm.read",
        "tasks.read",
        "tasks.write",
        "automation.run",
        "ai.use",
        "agent.execute",
    ),
    "partner": ("crm.read", "knowledge.read", "files.upload", "ai.use"),
    "dealer": ("crm.read", "crm.write", "erp.read", "ai.use"),
    "client": ("crm.read", "knowledge.read", "ai.use", "calendar.read"),
    "guest": ("knowledge.read",),
}


def all_permissions() -> list[PermissionDef]:
    return list(PLATFORM_PERMISSIONS.values())


def permissions_for_roles(roles: list[str]) -> list[str]:
    from platform_identity.registries.role_registry import normalize_roles

    perms: set[str] = set(defaults_for_roles(roles))
    for role in normalize_roles(roles):
        perms.update(_EXTENDED_DEFAULTS.get(role, ()))
    return sorted(perms)


def normalize_platform_permission(raw: str | None) -> str | None:
    if not raw:
        return None
    key = str(raw).strip().lower()
    if key in PLATFORM_PERMISSIONS:
        return key
    for code, d in PLATFORM_PERMISSIONS.items():
        if key == code or key in {a.lower() for a in d.aliases}:
            return code
    return normalize_permission(raw)


__all__ = [
    "PLATFORM_PERMISSIONS",
    "ROLE_PERMISSION_DEFAULTS",
    "PermissionDef",
    "all_permissions",
    "expand_permissions",
    "normalize_platform_permission",
    "permissions_for_roles",
]
