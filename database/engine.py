# PostgreSQL AsyncEngine — SQLAlchemy 2.x + asyncpg.

from __future__ import annotations

import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

load_dotenv()

DEFAULT_DATABASE_URL = (
    "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_ecosystem"
)

DATABASE_URL: str = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)

_engine: AsyncEngine | None = None


def get_engine(*, force_new: bool = False) -> AsyncEngine:
    """Return shared AsyncEngine with connection pooling."""
    global _engine
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
    url = DATABASE_URL
    if "+asyncpg" in url:
        return url.replace("+asyncpg", "+psycopg2", 1)
    return url


def is_postgres_configured() -> bool:
    return bool(DATABASE_URL and "postgresql" in DATABASE_URL)
