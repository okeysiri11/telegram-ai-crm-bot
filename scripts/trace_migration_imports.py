"""Trace import graph for Alembic migration bootstrap (no legacy SQLite)."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FORBIDDEN = (
    "database_legacy",
    "database_legacy.py",
    "handlers",
    "bot.py",
    "services",
)


def trace_migration_bootstrap() -> dict:
    before = set(sys.modules)
    from database.base import Base

    importlib.import_module("database.migration_models").load_all_models()
    after = set(sys.modules) - before

    loaded = sorted(
        name
        for name in after
        if name.startswith("database") or name.startswith("sqlalchemy")
    )
    forbidden_hits = sorted(
        name
        for name in sys.modules
        if any(token in name for token in FORBIDDEN)
        and name not in before
    )

    return {
        "base_import": "OK",
        "loaded_model_modules": loaded,
        "loaded_model_count": len(
            [m for m in loaded if m.startswith("database.models.")]
        ),
        "metadata_tables_count": len(Base.metadata.sorted_tables),
        "forbidden_imports": forbidden_hits,
        "legacy_free": len(forbidden_hits) == 0,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(trace_migration_bootstrap(), indent=2))
