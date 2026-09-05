"""Recruiting RBAC — additive; platform_owner is never denied."""

from __future__ import annotations

from typing import Any

RECRUITING_ROLES: dict[str, dict[str, Any]] = {
    "owner": {
        "id": "owner",
        "label_ru": "Владелец",
        "permissions": {"view", "create", "edit", "qualify", "convert", "merge", "admin"},
    },
    "recruiter": {
        "id": "recruiter",
        "label_ru": "Рекрутер",
        "permissions": {"view", "create", "edit", "qualify", "convert", "merge"},
    },
    "hiring_manager": {
        "id": "hiring_manager",
        "label_ru": "Нанимающий менеджер",
        "permissions": {"view", "create", "edit", "qualify"},
    },
    "observer": {
        "id": "observer",
        "label_ru": "Наблюдатель",
        "permissions": {"view"},
    },
    "platform_owner": {
        "id": "platform_owner",
        "label_ru": "Владелец платформы",
        "permissions": {"view", "create", "edit", "qualify", "convert", "merge", "admin"},
    },
}

ACTION_PERMISSION = {
    "list": "view",
    "get": "view",
    "create": "create",
    "update": "edit",
    "qualify": "qualify",
    "convert": "convert",
    "merge": "merge",
    "admin": "admin",
}


def normalize_role(role: str | None) -> str:
    raw = (role or "recruiter").strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "владелец": "owner",
        "рекрутер": "recruiter",
        "hr": "recruiter",
        "нанимающий_менеджер": "hiring_manager",
        "manager": "hiring_manager",
        "hiringmanager": "hiring_manager",
        "наблюдатель": "observer",
        "viewer": "observer",
        "read_only": "observer",
        "platformowner": "platform_owner",
        "owner_platform": "platform_owner",
        "company_owner": "owner",
        "admin": "owner",
        "administrator": "owner",
    }
    raw = aliases.get(raw, raw)
    if raw in RECRUITING_ROLES:
        return raw
    return "recruiter"


def can(role: str | None, action: str) -> bool:
    role_id = normalize_role(role)
    if role_id == "platform_owner":
        return True
    need = ACTION_PERMISSION.get(action, action)
    perms = RECRUITING_ROLES.get(role_id, RECRUITING_ROLES["observer"])["permissions"]
    return need in perms


def require(role: str | None, action: str) -> dict[str, Any] | None:
    if can(role, action):
        return None
    return {
        "ok": False,
        "error": "forbidden",
        "message_ru": f"Роль «{RECRUITING_ROLES[normalize_role(role)]['label_ru']}» не может выполнить действие: {action}",
        "role": normalize_role(role),
    }


ADS_PROVIDERS = ("meta", "google", "tiktok")
ADS_ADMIN_ACTIONS = {
    "connect",
    "reconnect",
    "disable",
    "disconnect",
    "configure",
    "oauth",
    "select_account",
    "select",
    "refresh",
    "refresh_credentials",
    "enable_sync",
    "disable_sync",
    "sync",
    "sync-metrics",
    "sync-campaigns",
}


def require_provider_admin(role: str | None, provider: str | None = None, action: str | None = None) -> dict[str, Any] | None:
    """Owner/admin only for ads credential mutations. Messaging keeps update."""
    key = (provider or "").strip().lower()
    act = (action or "admin").strip().lower()
    if key in ADS_PROVIDERS and (action is None or act in ADS_ADMIN_ACTIONS):
        denied = require(role, "admin")
        if denied:
            denied["message_ru"] = "Только владелец или администратор может менять подключение рекламного провайдера."
        return denied
    return require(role, "update")


def roles_catalog() -> list[dict[str, Any]]:
    return [
        {"id": r["id"], "label_ru": r["label_ru"], "permissions": sorted(r["permissions"])}
        for r in RECRUITING_ROLES.values()
        if r["id"] != "platform_owner"
    ]
