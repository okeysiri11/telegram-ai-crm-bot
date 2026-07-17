# Handler auth helpers — PostgreSQL-only (replaces `from database import` in handlers).

from __future__ import annotations

from services.audit_service import audit_service
from services.role_service import role_service


async def has_permission(telegram_id: int, permission: str) -> bool:
    return await role_service.has_permission(telegram_id, permission)


def has_permission_sync(telegram_id: int, permission: str) -> bool:
    from database.async_bridge import run_async

    result = run_async(role_service.has_permission(telegram_id, permission))
    if hasattr(result, "__await__"):
        return False
    return bool(result)


def log_audit(user_id: int, action: str, module: str, details: str = "") -> None:
    audit_service.log_sync(user_id, action, module, details)
