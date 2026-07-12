# Database package — PostgreSQL ORM infrastructure + lazy legacy SQLite re-exports.

from __future__ import annotations

from typing import Any

_legacy_module: Any | None = None


def _get_legacy_module():
    global _legacy_module
    if _legacy_module is None:
        import database_legacy as mod

        _legacy_module = mod
    return _legacy_module


def __getattr__(name: str) -> Any:
    return getattr(_get_legacy_module(), name)


def __dir__() -> list[str]:
    return dir(_get_legacy_module())
