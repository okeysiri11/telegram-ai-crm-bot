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


def get_engine(*, force_new: bool = False) -> AsyncEngine:
    """Return shared AsyncEngine with connection pooling."""
    global _engine, DATABASE_URL
    DATABASE_URL = _database_url()
    if _engine is not None and not force_new:
        return _engine

    _engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        pool_size=20,
        max_overflow=40,
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
