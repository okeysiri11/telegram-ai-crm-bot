# Async SQLAlchemy session factory and health checks.

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.connection import dispose_engine, get_engine, is_postgres_configured
from database.base import Base

_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
    return _session_factory


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    session = get_session_factory()()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def init_db() -> None:
    """Create tables from metadata (dev/bootstrap; prefer Alembic in production)."""
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def check_db_health() -> dict:
    """PostgreSQL connectivity probe for /system/db-health."""
    if not is_postgres_configured():
        return {
            "ok": False,
            "status": "unconfigured",
            "driver": "asyncpg",
            "error": "POSTGRES_* environment variables are incomplete",
        }

    try:
        async with get_session() as session:
            version_row = await session.execute(text("SELECT version()"))
            pg_version = version_row.scalar_one()
            ping_row = await session.execute(text("SELECT 1 AS ok"))
            ping = ping_row.scalar_one()

        engine = get_engine()
        pool = engine.pool
        pool_status = {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
        }

        return {
            "ok": ping == 1,
            "status": "healthy",
            "driver": "asyncpg",
            "postgres_version": pg_version,
            "pool": pool_status,
        }
    except Exception as exc:
        return {
            "ok": False,
            "status": "unhealthy",
            "driver": "asyncpg",
            "error": str(exc),
        }


async def shutdown_db() -> None:
    global _session_factory
    _session_factory = None
    await dispose_engine()
