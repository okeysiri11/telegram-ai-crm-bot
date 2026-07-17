#!/usr/bin/env python3
"""Fail CI when production code uses SQLite or legacy database patterns."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN = {
    "sqlite3.connect": re.compile(r"sqlite3\.connect\s*\("),
    "memory.db": re.compile(r"memory\.db"),
    "cursor.execute": re.compile(r"cursor\.execute\s*\("),
}

ALLOWLIST_PREFIXES = (
    "database_legacy.py",
    "scripts/",
    "tests/",
    "migrations/",
    "services/platform_test.py",
    "services/platform_hardening_test.py",
    "services/platform_readiness_test_suite.py",
    "services/event_bus_test.py",
)

ALLOWLIST_FILES = frozenset({
    "scripts/audit_sqlite_usage.py",
    "scripts/check_no_sqlite.py",
})


def is_allowed(rel: str) -> bool:
    if rel in ALLOWLIST_FILES:
        return True
    return any(rel.startswith(p) or rel == p for p in ALLOWLIST_PREFIXES)


def scan() -> list[tuple[str, str, int]]:
    violations: list[tuple[str, str, int]] = []
    for path in ROOT.rglob("*.py"):
        rel = path.relative_to(ROOT).as_posix()
        if is_allowed(rel):
            continue
        if "venv" in rel or "__pycache__" in rel:
            continue
        for line_no, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            for name, pattern in FORBIDDEN.items():
                if pattern.search(line):
                    violations.append((rel, name, line_no))
    return violations


def main() -> int:
    violations = scan()
    if not violations:
        print("OK: no forbidden SQLite patterns in production code")
        return 0
    print("Forbidden SQLite patterns in production code:")
    for rel, name, line_no in violations:
        print(f"  {rel}:{line_no} — {name}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
