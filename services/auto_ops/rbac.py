"""AUTO 1.0 private desk RBAC — Director / Accountant / Manager / Admin.

Permissions are enforced in the service layer, not only in the UI.
"""

from __future__ import annotations

from typing import Any

AUTO_ROLES: dict[str, dict[str, Any]] = {
    "auto_director": {
        "id": "auto_director",
        "label_ru": "Директор",
        "permissions": {
            "view",
            "create",
            "edit",
            "delete",
            "finance",
            "finance_write",
            "documents",
            "photos",
            "tasks",
            "clients",
            "reports",
            "admin",
            "vin_override",
            "audit",
            "pii",
        },
    },
    "auto_accountant": {
        "id": "auto_accountant",
        "label_ru": "Бухгалтер",
        "permissions": {
            "view",
            "finance",
            "finance_write",
            "documents",
            "reports",
            "audit",
        },
    },
    "auto_manager": {
        "id": "auto_manager",
        "label_ru": "Менеджер",
        "permissions": {
            "view",
            "create",
            "edit",
            "documents",
            "photos",
            "tasks",
            "clients",
        },
    },
    "auto_forwarder": {
        "id": "auto_forwarder",
        "label_ru": "Экспедитор",
        "permissions": {
            "view",
            "create",
            "edit",
            "documents",
            "photos",
            "tasks",
            "clients",
        },
    },
    "auto_customs": {
        "id": "auto_customs",
        "label_ru": "Ответственный за таможню",
        "permissions": {
            "view",
            "create",
            "edit",
            "documents",
            "photos",
            "tasks",
            "clients",
        },
    },
    "auto_admin": {
        "id": "auto_admin",
        "label_ru": "Администратор",
        "permissions": {
            "view",
            "admin",
            "vin_override",
            "audit",
            "pii",
        },
    },
    "platform_owner": {
        "id": "platform_owner",
        "label_ru": "Владелец платформы",
        "permissions": {
            "view",
            "create",
            "edit",
            "delete",
            "finance",
            "finance_write",
            "documents",
            "photos",
            "tasks",
            "clients",
            "reports",
            "admin",
            "vin_override",
            "audit",
            "pii",
        },
    },
}

# Clients / guests never access the private Auto OS.
DENIED_ROLES = frozenset({"client", "customer", "guest", "anonymous", "buyer"})

ACTION_PERMISSION = {
    "list": "view",
    "get": "view",
    "create": "create",
    "update": "edit",
    "delete": "delete",
    "finance": "finance",
    "finance_write": "finance_write",
    "documents": "documents",
    "photos": "photos",
    "tasks": "tasks",
    "clients": "clients",
    "reports": "reports",
    "admin": "admin",
    "vin_override": "vin_override",
    "audit": "audit",
    "pii": "pii",
}


def normalize_role(role: str | None) -> str:
    raw = (role or "auto_manager").strip().lower().replace(" ", "_").replace("-", "_")
    if raw in DENIED_ROLES:
        return "denied"
    aliases = {
        "director": "auto_director",
        "директор": "auto_director",
        "owner": "auto_director",
        "владелец": "auto_director",
        "accountant": "auto_accountant",
        "бухгалтер": "auto_accountant",
        "manager": "auto_manager",
        "менеджер": "auto_manager",
        "admin": "auto_admin",
        "administrator": "auto_admin",
        "администратор": "auto_admin",
        "platformowner": "platform_owner",
        "platform_owner": "platform_owner",
        "auto_director": "auto_director",
        "auto_accountant": "auto_accountant",
        "auto_manager": "auto_manager",
        "auto_forwarder": "auto_forwarder",
        "forwarder": "auto_forwarder",
        "экспедитор": "auto_forwarder",
        "auto_customs": "auto_customs",
        "customs": "auto_customs",
        "customs_broker": "auto_customs",
        "таможня": "auto_customs",
        "брокер": "auto_customs",
        "accountant_reviewer": "auto_accountant",
        "reviewer": "auto_accountant",
        "ревьюер": "auto_accountant",
        "auto_admin": "auto_admin",
    }
    raw = aliases.get(raw, raw)
    if raw in AUTO_ROLES:
        return raw
    return "auto_manager"


def can(role: str | None, action: str) -> bool:
    role_id = normalize_role(role)
    if role_id == "denied":
        return False
    if role_id == "platform_owner":
        return True
    need = ACTION_PERMISSION.get(action, action)
    return need in AUTO_ROLES.get(role_id, {}).get("permissions", set())


def require(role: str | None, action: str) -> dict[str, Any] | None:
    if can(role, action):
        return None
    role_id = normalize_role(role)
    if role_id == "denied":
        return {
            "ok": False,
            "error": "forbidden",
            "message_ru": "Авто — закрытое рабочее пространство. Доступ только для сотрудников компании.",
            "role": role_id,
        }
    label = AUTO_ROLES.get(role_id, {}).get("label_ru", role_id)
    return {
        "ok": False,
        "error": "forbidden",
        "message_ru": f"Роль «{label}» не может выполнить действие: {action}",
        "role": role_id,
    }


def roles_catalog() -> list[dict[str, Any]]:
    return [
        {"id": r["id"], "label_ru": r["label_ru"], "permissions": sorted(r["permissions"])}
        for r in AUTO_ROLES.values()
        if r["id"] != "platform_owner"
    ]
