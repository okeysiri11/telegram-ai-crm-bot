# PostgreSQL async engine and connection pooling (SQLAlchemy 2 + asyncpg).

from __future__ import annotations

import os
from urllib.parse import quote_plus

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

DEFAULT_POOL_SIZE = 10
DEFAULT_MAX_OVERFLOW = 20
DEFAULT_POOL_TIMEOUT = 30
DEFAULT_POOL_RECYCLE = 1800


def _env(name: str, default: str = "") -> str:
    return (os.getenv(name) or default).strip()


def get_postgres_settings() -> dict[str, str | int]:
    return {
        "host": _env("POSTGRES_HOST", "localhost"),
        "port": int(_env("POSTGRES_PORT", "5432")),
        "database": _env("POSTGRES_DB", "bidex"),
        "user": _env("POSTGRES_USER", "bidex"),
        "password": _env("POSTGRES_PASSWORD", ""),
        "pool_size": int(_env("POSTGRES_POOL_SIZE", str(DEFAULT_POOL_SIZE))),
        "max_overflow": int(_env("POSTGRES_MAX_OVERFLOW", str(DEFAULT_MAX_OVERFLOW))),
        "pool_timeout": int(_env("POSTGRES_POOL_TIMEOUT", str(DEFAULT_POOL_TIMEOUT))),
        "pool_recycle": int(_env("POSTGRES_POOL_RECYCLE", str(DEFAULT_POOL_RECYCLE))),
    }


def build_database_url(
    *,
    host: str | None = None,
    port: int | None = None,
    database: str | None = None,
    user: str | None = None,
    password: str | None = None,
) -> str:
    settings = get_postgres_settings()
    host = host or str(settings["host"])
    port = port or int(settings["port"])
    database = database or str(settings["database"])
    user = user or str(settings["user"])
    password = password if password is not None else str(settings["password"])
    safe_user = quote_plus(user)
    safe_password = quote_plus(password)
    return f"postgresql+asyncpg://{safe_user}:{safe_password}@{host}:{port}/{database}"


_engine: AsyncEngine | None = None


def get_engine(*, force_new: bool = False) -> AsyncEngine:
    """Return shared async engine with connection pooling."""
    global _engine
    if _engine is not None and not force_new:
        return _engine

    settings = get_postgres_settings()
    _engine = create_async_engine(
        build_database_url(),
        pool_size=int(settings["pool_size"]),
        max_overflow=int(settings["max_overflow"]),
        pool_timeout=int(settings["pool_timeout"]),
        pool_recycle=int(settings["pool_recycle"]),
        pool_pre_ping=True,
        echo=_env("SQLALCHEMY_ECHO", "").lower() in {"1", "true", "yes"},
    )
    return _engine


async def dispose_engine() -> None:
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None


def is_postgres_configured() -> bool:
    settings = get_postgres_settings()
    return bool(settings["host"] and settings["database"] and settings["user"])
