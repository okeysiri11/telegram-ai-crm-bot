# PostgreSQL AsyncEngine — SQLAlchemy 2.x + asyncpg.

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from platform_configuration.configuration_center import configuration_center

DEFAULT_DATABASE_URL = (
    "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_ecosystem"
)

_engine: AsyncEngine | None = None


def _database_url() -> str:
    return configuration_center.settings.database.url or DEFAULT_DATABASE_URL


DATABASE_URL: str = _database_url()


def _pool_kwargs() -> dict:
    """Sprint 37.3 — env-tunable pool via ConfigurationCenter (safe defaults preserved)."""
    try:
        db = configuration_center.settings.database
        return {
            "pool_size": int(getattr(db, "pool_size", 20) or 20),
            "max_overflow": int(getattr(db, "max_overflow", 40) or 40),
            "pool_timeout": float(getattr(db, "pool_timeout", 30.0) or 30.0),
            "pool_recycle": int(getattr(db, "pool_recycle", 1800) or 1800),
        }
    except Exception:  # noqa: BLE001
        return {
            "pool_size": 20,
            "max_overflow": 40,
            "pool_timeout": 30.0,
            "pool_recycle": 1800,
        }


def get_engine(*, force_new: bool = False) -> AsyncEngine:
    """Return shared AsyncEngine with connection pooling."""
    global _engine, DATABASE_URL
    DATABASE_URL = _database_url()
    if _engine is not None and not force_new:
        return _engine

    pool = _pool_kwargs()
    _engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        pool_size=pool["pool_size"],
        max_overflow=pool["max_overflow"],
        pool_timeout=pool["pool_timeout"],
        pool_recycle=pool["pool_recycle"],
    )
    return _engine


async def dispose_engine() -> None:
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None


def get_sync_database_url() -> str:
    """Sync URL for Alembic / psycopg2 tooling."""
    url = _database_url()
    if "+asyncpg" in url:
        return url.replace("+asyncpg", "+psycopg2", 1)
    return url


def is_postgres_configured() -> bool:
    url = _database_url()
    return bool(url and "postgresql" in url)


def pool_diagnostics() -> dict:
    """Non-invasive pool snapshot for performance / readiness reports."""
    engine = get_engine()
    pool = engine.pool
    cfg = _pool_kwargs()
    checked_in = pool.checkedin() if hasattr(pool, "checkedin") else None
    checked_out = pool.checkedout() if hasattr(pool, "checkedout") else None
    overflow = pool.overflow() if hasattr(pool, "overflow") else None
    return {
        "pool_size": cfg["pool_size"],
        "max_overflow": cfg["max_overflow"],
        "pool_timeout": cfg["pool_timeout"],
        "pool_recycle": cfg["pool_recycle"],
        "pool_pre_ping": True,
        "checked_in": checked_in,
        "checked_out": checked_out,
        "overflow": overflow,
    }
