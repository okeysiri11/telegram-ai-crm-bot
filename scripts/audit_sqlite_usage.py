#!/usr/bin/env python3
"""Audit SQLite and legacy database imports across the codebase."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PATTERNS = {
    "sqlite3": re.compile(r"\bsqlite3\b"),
    "memory.db": re.compile(r"memory\.db"),
    "cursor.execute": re.compile(r"cursor\.execute\s*\("),
    "from database import": re.compile(r"from database import"),
    "ensure_user": re.compile(r"\bensure_user\s*\("),
    "create_request": re.compile(r"\bcreate_request\s*\("),
}

SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "migrations/versions"}


def scan() -> dict[str, list[str]]:
    findings: dict[str, list[str]] = {k: [] for k in PATTERNS}
    for path in ROOT.rglob("*.py"):
        rel = path.relative_to(ROOT).as_posix()
        if any(part in rel for part in SKIP_DIRS):
            continue
        if rel.startswith("migrations/versions/"):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for name, pattern in PATTERNS.items():
            if pattern.search(text):
                findings[name].append(rel)
    return findings


def main() -> int:
    findings = scan()
    print("# SQLite / Legacy Database Audit\n")
    for name, files in findings.items():
        print(f"## {name} ({len(files)} files)")
        for f in sorted(set(files)):
            print(f"  - {f}")
        print()
    legacy_count = len(findings["from database import"])
    if legacy_count:
        print(f"WARNING: {legacy_count} files still use `from database import` — migrate to services.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
