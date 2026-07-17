# Database package — PostgreSQL production API (SQLite legacy opt-in only).

from __future__ import annotations

import logging
from typing import Any

from config import POSTGRES_ONLY

logger = logging.getLogger(__name__)

_legacy_module: Any | None = None

# Critical paths — always PostgreSQL.
_PG_SHIMS = frozenset({
    "ensure_user",
    "create_request",
    "log_audit",
    "has_permission",
    "get_user_roles",
    "assign_role",
})


def _get_legacy_module():
    global _legacy_module
    if POSTGRES_ONLY:
        raise RuntimeError(
            "SQLite legacy (database_legacy) is disabled when POSTGRES_ONLY=true. "
            "Use services/* and repositories/*."
        )
    if _legacy_module is None:
        import database_legacy as mod

        _legacy_module = mod
    return _legacy_module


def _ensure_user_pg(telegram_id: int, full_name: str = "", username: str = ""):
    from database.async_bridge import run_async
    from services.user_service import user_service

    result = run_async(
        user_service.ensure_user(
            telegram_id=telegram_id,
            full_name=full_name,
            username=username,
        )
    )
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

    result = run_async(
        request_service.create_request(
            vertical="agro",
            client_telegram_id=client_id,
            client_name=client_name,
            product=product,
            description=request_text,
        )
    )
    if hasattr(result, "__await__"):
        return None
    return result.get("request_number") if isinstance(result, dict) else result


def _log_audit_pg(user_id: int, action: str, module: str, details: str = ""):
    from services.audit_service import audit_service

    audit_service.log_sync(user_id, action, module, details)


def _has_permission_pg(telegram_id: int, permission: str) -> bool:
    from database.async_bridge import run_async
    from services.role_service import role_service

    result = run_async(role_service.has_permission(telegram_id, permission))
    if hasattr(result, "__await__"):
        return False
    return bool(result)


def _get_user_roles_pg(telegram_id: int) -> list[str]:
    from database.async_bridge import run_async
    from services.user_service import user_service

    result = run_async(user_service.list_roles(telegram_id=telegram_id))
    if hasattr(result, "__await__"):
        return []
    return list(result or [])


def _assign_role_pg(telegram_id: int, role_name: str) -> bool:
    from database.async_bridge import run_async
    from services.user_service import user_service

    result = run_async(
        user_service.assign_role(telegram_id=telegram_id, role_code=role_name)
    )
    return result is not None


_SHIM_IMPL = {
    "ensure_user": _ensure_user_pg,
    "create_request": _create_request_pg,
    "log_audit": _log_audit_pg,
    "has_permission": _has_permission_pg,
    "get_user_roles": _get_user_roles_pg,
    "assign_role": _assign_role_pg,
}


def __getattr__(name: str) -> Any:
    if name in _PG_SHIMS:
        return _SHIM_IMPL[name]
    import database_legacy as legacy

    if hasattr(legacy, name):
        attr = getattr(legacy, name)
        if POSTGRES_ONLY and name not in _PG_SHIMS:
            logger.debug("Legacy database.%s accessed under POSTGRES_ONLY", name)
        return attr
    raise AttributeError(
        f"module 'database' has no attribute {name!r}. "
        f"Use services layer (docs/services.md)."
    )


def __dir__() -> list[str]:
    if POSTGRES_ONLY:
        return sorted(_PG_SHIMS)
    return dir(_get_legacy_module())
