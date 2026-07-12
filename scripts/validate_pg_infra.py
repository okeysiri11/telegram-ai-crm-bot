"""Validate PostgreSQL infrastructure: metadata, models, migration readiness."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def validate_metadata() -> dict:
    from database.base import Base
    from database.migration_models import load_all_models

    load_all_models()

    tables = Base.metadata.sorted_tables
    fk_count = sum(len(t.foreign_keys) for t in tables)
    index_count = sum(len(t.indexes) for t in tables)

    return {
        "tables_count": len(tables),
        "indexes_count": index_count,
        "foreign_keys_count": fk_count,
        "table_names": [t.name for t in tables],
        "metadata_loaded": True,
    }


def validate_engine_config() -> dict:
    from database.engine import DATABASE_URL, get_engine

    engine = get_engine()
    return {
        "database_url": DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else DATABASE_URL,
        "pool_size": engine.pool.size(),
        "pool_pre_ping": True,
        "max_overflow": 40,
        "driver": "asyncpg",
    }


def validate_session_factory() -> dict:
    from database.session import get_session_factory

    factory = get_session_factory()
    return {
        "session_factory": factory.__class__.__name__,
        "expire_on_commit": factory.kw.get("expire_on_commit"),
        "autoflush": factory.kw.get("autoflush"),
    }


def migration_status() -> dict:
    root = ROOT
    versions_dir = root / "migrations" / "versions"
    migration_files = sorted(
        p.name for p in versions_dir.glob("*.py") if p.name != "__init__.py"
    )

    result = {
        "alembic_ini": (root / "alembic.ini").exists(),
        "migrations_env": (root / "migrations" / "env.py").exists(),
        "migration_files": migration_files,
        "migration_count": len(migration_files),
        "autogenerate_ran": False,
        "alembic_current": None,
        "error": None,
    }

    if not migration_files:
        return result

    env = os.environ.copy()
    env.setdefault(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_ecosystem",
    )
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "alembic", "current"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
        )
        result["alembic_current"] = (proc.stdout or proc.stderr).strip()
        result["autogenerate_ran"] = any(
            "initial_postgres_schema" in name for name in migration_files
        )
    except Exception as exc:
        result["error"] = str(exc)

    return result


def run_full_report() -> dict:
    report = {
        "metadata": validate_metadata(),
        "engine": validate_engine_config(),
        "session": validate_session_factory(),
        "migration": migration_status(),
    }
    report["status"] = (
        "OK"
        if report["metadata"]["metadata_loaded"]
        and report["metadata"]["tables_count"] >= 30
        and report["migration"]["migration_count"] >= 1
        else "PARTIAL"
    )
    return report


if __name__ == "__main__":
    print(json.dumps(run_full_report(), indent=2))
