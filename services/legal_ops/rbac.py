"""Lawyer RBAC — Sprint 51.0 (additive; does not weaken platform-owner)."""

from __future__ import annotations

from typing import Any

# Suggested Lawyer vertical roles (RU labels for UI)
LAWYER_ROLES: dict[str, dict[str, Any]] = {
    "owner": {
        "id": "owner",
        "label_ru": "Владелец",
        "permissions": {"view", "create", "edit", "approve", "delete", "admin", "ai", "sync"},
    },
    "managing_partner": {
        "id": "managing_partner",
        "label_ru": "Управляющий партнер",
        "permissions": {"view", "create", "edit", "approve", "delete", "admin", "ai", "sync"},
    },
    "lawyer": {
        "id": "lawyer",
        "label_ru": "Юрист",
        "permissions": {"view", "create", "edit", "approve", "ai", "sync"},
    },
    "paralegal": {
        "id": "paralegal",
        "label_ru": "Помощник юриста",
        "permissions": {"view", "create", "edit", "ai"},
    },
    "admin": {
        "id": "admin",
        "label_ru": "Администратор",
        "permissions": {"view", "create", "edit", "admin", "sync"},
    },
    "observer": {
        "id": "observer",
        "label_ru": "Наблюдатель",
        "permissions": {"view"},
    },
    # Platform owner always allowed
    "platform_owner": {
        "id": "platform_owner",
        "label_ru": "Владелец платформы",
        "permissions": {"view", "create", "edit", "approve", "delete", "admin", "ai", "sync"},
    },
}

ACTION_PERMISSION = {
    "list": "view",
    "get": "view",
    "create": "create",
    "update": "edit",
    "approve": "approve",
    "archive": "edit",
    "restore": "edit",
    "ai": "ai",
    "sync": "sync",
    "admin": "admin",
}


def normalize_role(role: str | None) -> str:
    raw = (role or "lawyer").strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "владелец": "owner",
        "управляющий_партнер": "managing_partner",
        "управляющийпартнер": "managing_partner",
        "юрист": "lawyer",
        "помощник_юриста": "paralegal",
        "помощникюриста": "paralegal",
        "администратор": "admin",
        "administrator": "admin",
        "наблюдатель": "observer",
        "viewer": "observer",
        "read_only": "observer",
        "manager": "managing_partner",
        "platformowner": "platform_owner",
        "owner_platform": "platform_owner",
        "company_owner": "owner",
    }
    raw = aliases.get(raw, raw)
    if raw in LAWYER_ROLES:
        return raw
    return "lawyer"


def can(role: str | None, action: str) -> bool:
    role_id = normalize_role(role)
    need = ACTION_PERMISSION.get(action, action)
    perms = LAWYER_ROLES.get(role_id, LAWYER_ROLES["observer"])["permissions"]
    if role_id == "platform_owner":
        return True
    return need in perms


def require(role: str | None, action: str) -> dict[str, Any] | None:
    """Return error dict if denied, else None."""
    if can(role, action):
        return None
    return {
        "ok": False,
        "error": "forbidden",
        "message_ru": f"Роль «{LAWYER_ROLES[normalize_role(role)]['label_ru']}» не может выполнить действие: {action}",
        "role": normalize_role(role),
    }


def roles_catalog() -> list[dict[str, Any]]:
    return [
        {"id": r["id"], "label_ru": r["label_ru"], "permissions": sorted(r["permissions"])}
        for r in LAWYER_ROLES.values()
        if r["id"] != "platform_owner"
    ]
