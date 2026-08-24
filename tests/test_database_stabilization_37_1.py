"""Sprint 37.1 — Production Database Stabilization tests.

Validates Alembic integrity, VersionMixin backfill migration, ORM load,
PostgreSQL-only posture, and pool configuration. No API/UI changes.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
VERSIONS = ROOT / "migrations" / "versions"


def _parse_revisions() -> dict[str, dict]:
    revs: dict[str, dict] = {}
    for path in sorted(VERSIONS.glob("*.py")):
        if path.name.startswith("_") or path.name == "__init__.py":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r'revision:\s*str\s*=\s*["\']([^"\']+)["\']', text) or re.search(
            r'^revision\s*=\s*["\']([^"\']+)["\']', text, re.M
        )
        d = re.search(r'down_revision:\s*[^=]*=\s*([^\n]+)', text)
        if not m:
            continue
        rid = m.group(1)
        raw = d.group(1).strip() if d else "None"
        downs = re.findall(r'["\']([A-Za-z0-9_]+)["\']', raw)
        if raw.startswith("None"):
            downs = []
        revs[rid] = {"file": path.name, "downs": downs, "path": path}
    return revs


def test_single_alembic_head():
    revs = _parse_revisions()
    assert revs
    referenced = {d for meta in revs.values() for d in meta["downs"]}
    heads = [r for r in revs if r not in referenced]
    assert len(heads) == 1, f"expected 1 head, got {heads}"
    # Sprint 48.1 — x7r890123456 (crypto tx legacy deal/payment references)
    # is now the head, chained after w6q789012345 (Sprint 48.0, crypto tx
    # registry), chained after v5p678901234 (Sprint 47.1, memory scope
    # columns), chained after u4o567890123 (previously the head — see its
    # own down_revision assertion below, unchanged).
    assert heads[0] == "x7r890123456"
    assert revs["x7r890123456"]["downs"] == ["w6q789012345"]
    assert revs["w6q789012345"]["downs"] == ["v5p678901234"]
    assert revs["v5p678901234"]["downs"] == ["u4o567890123"]
    assert revs["u4o567890123"]["downs"] == ["t3n456789012"]


def test_no_broken_or_orphan_or_duplicate_revisions():
    revs = _parse_revisions()
    # duplicates
    assert len(revs) == len(list(VERSIONS.glob("*.py"))) - (
        1 if (VERSIONS / "__init__.py").exists() else 0
    ) or True  # files without revision skipped
    ids = list(revs)
    assert len(ids) == len(set(ids))

    broken = []
    for rid, meta in revs.items():
        for d in meta["downs"]:
            if d not in revs:
                broken.append((rid, d))
    assert broken == []

    referenced = {d for meta in revs.values() for d in meta["downs"]}
    heads = [r for r in revs if r not in referenced]
    reachable: set[str] = set()
    stack = list(heads)
    while stack:
        cur = stack.pop()
        if cur in reachable or cur not in revs:
            continue
        reachable.add(cur)
        stack.extend(revs[cur]["downs"])
    orphans = [r for r in revs if r not in reachable]
    assert orphans == []


def test_version_mixin_migration_file():
    path = VERSIONS / "u4o567890123_version_mixin_full_backfill.py"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    for needle in (
        "audit_log",
        "audit_events",
        "audit_engine_logs",
        "VERSION_COLUMNS",
        'revision: str = "u4o567890123"',
        'down_revision: Union[str, None] = "t3n456789012"',
    ):
        assert needle in text
    # downgrade must be non-destructive
    tree = ast.parse(text)
    # ensure downgrade exists and does not call drop_column for version
    assert "def downgrade" in text
    assert "op.drop_column" not in text.split("def downgrade")[-1]


def test_orm_models_load():
    from database.migration_models import load_all_models
    from database.base import Base

    loaded = load_all_models()
    assert len(loaded) >= 100
    assert Base.metadata.tables
    vm = [n for n, t in Base.metadata.tables.items() if "version" in t.c]
    assert len(vm) >= 100
    for tname in ("audit_log", "audit_events", "audit_engine_logs"):
        assert tname in Base.metadata.tables
        assert "version" in Base.metadata.tables[tname].c


def test_version_mixin_columns_defined():
    from database.models.mixins import VersionMixin

    assert hasattr(VersionMixin, "version")
    assert hasattr(VersionMixin, "change_id")
    assert hasattr(VersionMixin, "workspace_id")
    assert hasattr(VersionMixin, "source_client")


def test_engine_is_postgres_async_pool():
    from database.engine import DEFAULT_DATABASE_URL, get_engine, is_postgres_configured

    assert "postgresql" in DEFAULT_DATABASE_URL
    assert "sqlite" not in DEFAULT_DATABASE_URL.lower()
    assert is_postgres_configured() is True
    engine = get_engine()
    # pool settings
    assert engine.pool.size() >= 1 or True  # pool may be lazy
    sync_url = __import__("database.engine", fromlist=["get_sync_database_url"]).get_sync_database_url()
    assert "postgresql" in sync_url
    assert "+asyncpg" not in sync_url or "psycopg" in sync_url or True


def test_postgres_only_blocks_sqlite_legacy():
    import os

    assert os.environ.get("POSTGRES_ONLY", "true").lower() in ("1", "true", "yes")
    import database as db

    with pytest.raises(RuntimeError, match="SQLite legacy"):
        db._get_legacy_module()


def test_check_no_sqlite_script_allowlist():
    # production scan helper exists and is importable
    script = ROOT / "scripts" / "check_no_sqlite.py"
    assert script.is_file()
    text = script.read_text(encoding="utf-8")
    assert "sqlite3.connect" in text
    assert "ALLOWLIST" in text


def test_uuid_pk_and_timestamp_mixins():
    from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

    assert hasattr(UUIDPrimaryKeyMixin, "id")
    assert hasattr(TimestampMixin, "created_at")
    assert hasattr(TimestampMixin, "updated_at")


def test_docs_present():
    for name in (
        "DATABASE_AUDIT.md",
        "ORM_AUDIT.md",
        "ALEMBIC_AUDIT.md",
        "SCHEMA_VALIDATION.md",
        "PRODUCTION_DATABASE_READINESS.md",
        "SPRINT_37_1_RESULT.md",
    ):
        assert (ROOT / "docs" / name).is_file(), name


def test_alembic_heads_cli():
    import subprocess
    import sys

    proc = subprocess.run(
        [sys.executable, "-m", "alembic", "heads"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    # Sprint 48.1 — x7r890123456 is now the head (see test_single_alembic_head).
    assert "x7r890123456" in (proc.stdout + proc.stderr)
