# Database package — PostgreSQL production API (SQLite legacy opt-in only).

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_legacy_module: Any | None = None


def _postgres_only() -> bool:
    try:
        from config import POSTGRES_ONLY

        return bool(POSTGRES_ONLY)
    except ImportError:
        # Partial bootstrap (config still loading); tests set POSTGRES_ONLY before import.
        return True

# Critical paths — always PostgreSQL.
_PG_SHIMS = frozenset({
    "ensure_user",
    "create_request",
    "log_audit",
    "has_permission",
    "get_user_roles",
    "assign_role",
    "get_user_profile",
    "save_profile_fields",
    "format_memory_context",
    "format_memory_text",
    "format_profile_text",
    "load_memory",
    "save_memory",
    "get_memory",
    "MEMORY_FIELDS",
})


def _get_legacy_module():
    global _legacy_module
    if _postgres_only():
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


def _memory_fields_pg():
    from services.user_memory_service import MEMORY_FIELDS

    return MEMORY_FIELDS


def _get_user_profile_pg(user_id: int) -> dict:
    from services.user_memory_service import get_user_profile

    return get_user_profile(user_id)


def _save_profile_fields_pg(user_id: int, fields: dict) -> None:
    from services.user_memory_service import save_profile_fields

    save_profile_fields(user_id, fields)


def _format_memory_context_pg(user_id: int) -> str:
    from services.user_memory_service import format_memory_context

    return format_memory_context(user_id)


def _format_memory_text_pg(user_id: int) -> str:
    from services.user_memory_service import format_memory_text

    return format_memory_text(user_id)


def _format_profile_text_pg(user_id: int) -> str:
    from services.user_memory_service import format_profile_text

    return format_profile_text(user_id)


def _load_memory_pg(user_id: int) -> dict:
    from services.user_memory_service import load_memory

    return load_memory(user_id)


def _save_memory_pg(user_id: int, key: str, value: str) -> None:
    from services.user_memory_service import save_memory

    save_memory(user_id, key, value)


def _get_memory_pg(user_id: int, key: str):
    from services.user_memory_service import get_memory

    return get_memory(user_id, key)


_SHIM_IMPL = {
    "ensure_user": _ensure_user_pg,
    "create_request": _create_request_pg,
    "log_audit": _log_audit_pg,
    "has_permission": _has_permission_pg,
    "get_user_roles": _get_user_roles_pg,
    "assign_role": _assign_role_pg,
    "get_user_profile": _get_user_profile_pg,
    "save_profile_fields": _save_profile_fields_pg,
    "format_memory_context": _format_memory_context_pg,
    "format_memory_text": _format_memory_text_pg,
    "format_profile_text": _format_profile_text_pg,
    "load_memory": _load_memory_pg,
    "save_memory": _save_memory_pg,
    "get_memory": _get_memory_pg,
    "MEMORY_FIELDS": _memory_fields_pg,
}


def __getattr__(name: str) -> Any:
    if name in _PG_SHIMS:
        impl = _SHIM_IMPL[name]
        # MEMORY_FIELDS is a constant dict; shim factory returns it.
        if name == "MEMORY_FIELDS" and callable(impl):
            return impl()
        return impl
    import database_legacy as legacy

    if hasattr(legacy, name):
        attr = getattr(legacy, name)
        if _postgres_only() and name not in _PG_SHIMS:
            logger.debug("Legacy database.%s accessed under POSTGRES_ONLY", name)
        return attr
    raise AttributeError(
        f"module 'database' has no attribute {name!r}. "
        f"Use services layer (docs/services.md)."
    )


def __dir__() -> list[str]:
    if _postgres_only():
        return sorted(_PG_SHIMS)
    return dir(_get_legacy_module())
