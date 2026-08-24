"""AGRO RBAC — permission-based roles (AGRO Production 1.0).

Director vs accountant separation per spec; permissions are extendable —
handlers check permissions, not role ids.
"""

from __future__ import annotations

from typing import Any

AGRO_ROLES: dict[str, dict[str, Any]] = {
    "agro_director": {
        "id": "agro_director",
        "label_ru": "Директор",
        "permissions": {
            "view", "create", "edit", "delete", "approve", "margins", "analytics",
            "finance", "export", "intel", "intel_admin", "ai", "admin", "tasks", "quality",
        },
    },
    "agro_manager": {
        "id": "agro_manager",
        "label_ru": "Менеджер",
        "permissions": {"view", "create", "edit", "tasks", "analytics", "intel", "ai"},
    },
    "agro_accountant": {
        "id": "agro_accountant",
        "label_ru": "Бухгалтер",
        # view counterparties/contracts, invoices/payments, attachments,
        # receivables/payables, export. No delete/admin/approve/intel_admin.
        "permissions": {"view", "finance", "export", "attach", "tasks"},
    },
    "agro_observer": {
        "id": "agro_observer",
        "label_ru": "Наблюдатель",
        "permissions": {"view"},
    },
    "agro_viewer": {
        "id": "agro_viewer",
        "label_ru": "Наблюдатель",
        "permissions": {"view"},
    },
    "agro_logistics": {
        "id": "agro_logistics",
        "label_ru": "Логист",
        "permissions": {"view", "create", "edit", "attach", "tasks"},
    },
    "agro_warehouse": {
        "id": "agro_warehouse",
        "label_ru": "Склад",
        "permissions": {"view", "create", "edit", "attach", "tasks"},
    },
    "agro_quality": {
        "id": "agro_quality",
        "label_ru": "Качество",
        "permissions": {"view", "create", "edit", "quality", "attach", "tasks"},
    },
    "agro_agronomist": {
        "id": "agro_agronomist",
        "label_ru": "Агроном",
        "permissions": {"view", "create", "edit", "attach", "tasks", "analytics"},
    },
    "agro_mechanic": {
        "id": "agro_mechanic",
        "label_ru": "Механик",
        "permissions": {"view", "create", "edit", "attach", "tasks"},
    },
    "platform_owner": {
        "id": "platform_owner",
        "label_ru": "Владелец платформы",
        "permissions": {
            "view", "create", "edit", "delete", "approve", "margins", "analytics",
            "finance", "export", "intel", "intel_admin", "ai", "admin", "tasks", "attach", "quality",
        },
    },
}

# Director implicitly can attach documents too.
AGRO_ROLES["agro_director"]["permissions"].add("attach")
AGRO_ROLES["agro_manager"]["permissions"].add("attach")

ACTION_PERMISSION = {
    "list": "view",
    "get": "view",
    "create": "create",
    "update": "edit",
    "archive": "edit",
    "restore": "edit",
    "delete": "delete",
    "approve": "approve",
    "margins": "margins",
    "finance": "finance",
    "export": "export",
    "intel": "intel",
    "intel_admin": "intel_admin",
    "ai": "ai",
    "admin": "admin",
    "attach": "attach",
    "tasks": "tasks",
    "quality": "quality",
}


def normalize_role(role: str | None) -> str:
    raw = (role or "agro_manager").strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "director": "agro_director",
        "директор": "agro_director",
        "owner": "agro_director",
        "владелец": "agro_director",
        "accountant": "agro_accountant",
        "бухгалтер": "agro_accountant",
        "manager": "agro_manager",
        "менеджер": "agro_manager",
        "observer": "agro_observer",
        "viewer": "agro_viewer",
        "agro_viewer": "agro_viewer",
        "наблюдатель": "agro_observer",
        "logistics": "agro_logistics",
        "логист": "agro_logistics",
        "логистика": "agro_logistics",
        "warehouse": "agro_warehouse",
        "склад": "agro_warehouse",
        "кладовщик": "agro_warehouse",
        "quality": "agro_quality",
        "качество": "agro_quality",
        "лаборатория": "agro_quality",
        "agronomist": "agro_agronomist",
        "агроном": "agro_agronomist",
        "mechanic": "agro_mechanic",
        "механик": "agro_mechanic",
        "platformowner": "platform_owner",
    }
    raw = aliases.get(raw, raw)
    if raw in AGRO_ROLES:
        return raw
    return "agro_manager"


def can(role: str | None, action: str) -> bool:
    role_id = normalize_role(role)
    if role_id == "platform_owner":
        return True
    need = ACTION_PERMISSION.get(action, action)
    return need in AGRO_ROLES.get(role_id, AGRO_ROLES["agro_observer"])["permissions"]


def require(role: str | None, action: str) -> dict[str, Any] | None:
    """Return error dict if denied, else None."""
    if can(role, action):
        return None
    return {
        "ok": False,
        "error": "forbidden",
        "message_ru": f"Роль «{AGRO_ROLES[normalize_role(role)]['label_ru']}» не может выполнить действие: {action}",
        "role": normalize_role(role),
    }


def roles_catalog() -> list[dict[str, Any]]:
    return [
        {"id": r["id"], "label_ru": r["label_ru"], "permissions": sorted(r["permissions"])}
        for r in AGRO_ROLES.values()
        if r["id"] != "platform_owner"
    ]
