# Database package — PostgreSQL facade; legacy SQLite blocked in production.

from __future__ import annotations

import logging
from typing import Any

from config import POSTGRES_ONLY

logger = logging.getLogger(__name__)

_legacy_module: Any | None = None

# Functions redirected to PostgreSQL services when POSTGRES_ONLY=true.
_PG_SHIMS = frozenset({
    "ensure_user",
    "create_request",
    "log_audit",
    "has_permission",
    "get_user_roles",
})


def _get_legacy_module():
    global _legacy_module
    if _legacy_module is None:
        import database_legacy as mod

        _legacy_module = mod
    return _legacy_module


def _ensure_user_pg(telegram_id: int, full_name: str = "", username: str = ""):
    from database.async_bridge import run_async
    from services.user_service import user_service

    coro = user_service.ensure_user(
        telegram_id=telegram_id,
        full_name=full_name,
        username=username,
    )
    result = run_async(coro)
    if hasattr(result, "__await__"):
        return None
    return result.get("id") if isinstance(result, dict) else result


def _create_request_pg(
    client_id: int,
    client_name: str,
    product: str,
    request_text: str,
    manager_id: int,
):
    from database.async_bridge import run_async
    from services.request_service import request_service

    coro = request_service.create_request(
        vertical="agro",
        client_telegram_id=client_id,
        client_name=client_name,
        product=product,
        description=request_text,
    )
    result = run_async(coro)
    if hasattr(result, "__await__"):
        return None
    return result.get("request_number") if isinstance(result, dict) else result


def _log_audit_pg(user_id: int, action: str, module: str, details: str = ""):
    from database.async_bridge import fire_and_forget
    from services.pg_platform_audit_engine import PlatformAuditEngineV1

    fire_and_forget(
        PlatformAuditEngineV1.log(
            event_type=action.upper(),
            entity_type=module,
            entity_id=details or str(user_id),
            user_id=user_id,
            payload={"action": action, "module": module, "details": details},
        )
    )


def _has_permission_pg(telegram_id: int, permission: str) -> bool:
    from database.async_bridge import run_async
    from services.role_service import role_service

    coro = role_service.has_permission(telegram_id, permission)
    result = run_async(coro)
    if hasattr(result, "__await__"):
        return False
    return bool(result)


def _get_user_roles_pg(telegram_id: int) -> list[str]:
    from database.async_bridge import run_async
    from services.user_service import user_service

    coro = user_service.list_roles(telegram_id=telegram_id)
    result = run_async(coro)
    if hasattr(result, "__await__"):
        return []
    return list(result or [])


_SHIM_IMPL = {
    "ensure_user": _ensure_user_pg,
    "create_request": _create_request_pg,
    "log_audit": _log_audit_pg,
    "has_permission": _has_permission_pg,
    "get_user_roles": _get_user_roles_pg,
}


def __getattr__(name: str) -> Any:
    if name in _PG_SHIMS:
        return _SHIM_IMPL[name]
    return getattr(_get_legacy_module(), name)


def __dir__() -> list[str]:
    if POSTGRES_ONLY:
        return sorted(_PG_SHIMS)
    return dir(_get_legacy_module())
