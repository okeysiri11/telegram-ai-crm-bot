# Backward-compatible re-exports — prefer database.engine.

from database.engine import (
    DATABASE_URL,
    DEFAULT_DATABASE_URL,
    dispose_engine,
    get_engine,
    get_sync_database_url,
    is_postgres_configured,
)


def build_database_url() -> str:
    return DATABASE_URL
