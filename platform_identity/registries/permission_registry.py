# Sprint 34.2A — Canonical permission registry (single source of truth).
#
# Module.action form. Legacy permission codes alias into these codes.
# Permission Engine DB rows remain the durable grant store; this registry
# is the vocabulary every client and seeder must converge on.

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PermissionDefinition:
    code: str
    description: str
    aliases: tuple[str, ...] = ()


# Primary vocabulary for multi-client platform (Sprint 34.2A).
PERMISSION_REGISTRY: dict[str, PermissionDefinition] = {
    "owner.full": PermissionDefinition("owner.full", "Full owner access", ("admin.access", "system.admin", "management.admin")),
    "crm.read": PermissionDefinition("crm.read", "Read CRM", ("leads.view", "clients.view", "requests.read")),
    "crm.write": PermissionDefinition(
        "crm.write",
        "Write CRM",
        ("leads.create", "leads.assign", "leads.update_status", "clients.update", "requests.write"),
    ),
    "erp.read": PermissionDefinition("erp.read", "Read ERP", ("inventory.view",)),
    "erp.write": PermissionDefinition("erp.write", "Write ERP", ("inventory.manage",)),
    "knowledge.read": PermissionDefinition("knowledge.read", "Read knowledge base", ()),
    "knowledge.write": PermissionDefinition("knowledge.write", "Write knowledge base", ()),
    "analytics.view": PermissionDefinition("analytics.view", "View analytics", ("analytics.view", "dashboard.read")),
    "documents.manage": PermissionDefinition("documents.manage", "Manage documents", ()),
    "ai.use": PermissionDefinition("ai.use", "Use AI features", ("ai.use", "ai.read")),
    "automation.run": PermissionDefinition("automation.run", "Run automations", ("workflow.write", "jobs.write")),
    "platform.config.read": PermissionDefinition(
        "platform.config.read",
        "Read platform configuration",
        ("configuration.read", "platform.config.read"),
    ),
    "platform.config.write": PermissionDefinition(
        "platform.config.write",
        "Write platform configuration",
        ("configuration.write", "platform.config.write"),
    ),
}


# Default grants per canonical role (used by Identity Core when DB grants empty).
ROLE_PERMISSION_DEFAULTS: dict[str, tuple[str, ...]] = {
    "owner": tuple(PERMISSION_REGISTRY.keys()),
    "ceo": tuple(PERMISSION_REGISTRY.keys()),
    "administrator": (
        "crm.read",
        "crm.write",
        "erp.read",
        "erp.write",
        "knowledge.read",
        "knowledge.write",
        "analytics.view",
        "documents.manage",
        "ai.use",
        "automation.run",
        "platform.config.read",
        "platform.config.write",
    ),
    "manager": (
        "crm.read",
        "crm.write",
        "erp.read",
        "analytics.view",
        "ai.use",
        "documents.manage",
        "knowledge.read",
    ),
    "employee": (
        "crm.read",
        "erp.read",
        "knowledge.read",
        "analytics.view",
        "ai.use",
    ),
    "operator": (
        "crm.read",
        "erp.read",
        "automation.run",
        "ai.use",
        "knowledge.read",
    ),
    "partner": (
        "crm.read",
        "knowledge.read",
        "documents.manage",
        "ai.use",
    ),
    "dealer": (
        "crm.read",
        "crm.write",
        "erp.read",
        "ai.use",
    ),
    "client": (
        "crm.read",
        "knowledge.read",
        "ai.use",
    ),
    "guest": (
        "knowledge.read",
    ),
}


_ALIAS_TO_CANONICAL: dict[str, str] = {}
for _code, _def in PERMISSION_REGISTRY.items():
    _ALIAS_TO_CANONICAL[_code.lower()] = _code
    for _a in _def.aliases:
        _ALIAS_TO_CANONICAL[_a.lower()] = _code


def normalize_permission(raw: str | None) -> str | None:
    if not raw:
        return None
    return _ALIAS_TO_CANONICAL.get(str(raw).strip().lower())


def expand_permissions(raw: list[str] | tuple[str, ...] | None) -> list[str]:
    """Normalize + expand legacy codes into canonical set."""
    out: list[str] = []
    seen: set[str] = set()
    for p in raw or []:
        c = normalize_permission(p) or p
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def defaults_for_roles(roles: list[str]) -> list[str]:
    from platform_identity.registries.role_registry import normalize_roles

    perms: set[str] = set()
    for role in normalize_roles(roles):
        perms.update(ROLE_PERMISSION_DEFAULTS.get(role, ()))
    return sorted(perms)


def all_permission_codes() -> list[str]:
    return list(PERMISSION_REGISTRY.keys())
