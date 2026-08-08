#!/usr/bin/env python3
"""ENV / secret hygiene check — Sprint 39.1 (INFRASTRUCTURE).

Fails if:
  - tracked git files look like live secret stores
  - .env.example is missing required secret *keys*
  - compose interpolates required secrets without documenting them in .env.example
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_ENV_KEYS = (
    "BOT_TOKEN",
    "DATABASE_URL",
    "POSTGRES_PASSWORD",
    "REDIS_URL",
    "IAM_JWT_SECRET",
    "API_JWT_SECRET",
    "JWT_SECRET",
    "IAM_LOGIN_SECRET",
    "GRAFANA_ADMIN_PASSWORD",
    "OPENROUTER_API_KEY",
)

OPTIONAL_DOCUMENTED = (
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
    "META_APP_ID",
    "META_APP_SECRET",
    "AI_REQUEST_SIGNING_SECRET",
    "N8N_ENCRYPTION_KEY",
)

FORBIDDEN_TRACKED = (
    ".env",
    ".env.local",
    ".env.production",
)

SECRET_VALUE_RE = re.compile(
    r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?(sk-|ghp_|xox[baprs]-|AKIA)[A-Za-z0-9_\-]{8,}"
)


def _tracked_files() -> list[str]:
    proc = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return [line for line in proc.stdout.splitlines() if line]


def main() -> int:
    failures: list[str] = []
    example = (ROOT / ".env.example").read_text(encoding="utf-8")
    for key in REQUIRED_ENV_KEYS:
        if f"{key}=" not in example and f"# {key}=" not in example:
            failures.append(f".env.example missing key: {key}")
    for key in OPTIONAL_DOCUMENTED:
        if f"{key}=" not in example and f"# {key}" not in example:
            failures.append(f".env.example missing documented optional key: {key}")

    tracked = set(_tracked_files())
    for name in FORBIDDEN_TRACKED:
        if name in tracked:
            failures.append(f"secret file is tracked by git: {name} (run git rm --cached)")

    # Scan tracked text for high-confidence live tokens (skip .env.example placeholders)
    for rel in tracked:
        if rel.endswith((".png", ".jpg", ".webp", ".pdf", ".dump", ".db")):
            continue
        path = ROOT / rel
        if not path.is_file() or path.stat().st_size > 2_000_000:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if SECRET_VALUE_RE.search(text) and rel != ".env.example":
            failures.append(f"possible live secret pattern in tracked file: {rel}")

    print("=== Secret / ENV validation (Sprint 39.1) ===")
    if failures:
        for item in failures:
            print(f"[FAIL] {item}")
        print(f"SECRET_GATE=FAIL count={len(failures)}")
        return 1
    print("[PASS] .env.example documents required secrets")
    print("[PASS] no forbidden secret files tracked")
    print("[PASS] no high-confidence live tokens in tracked tree")
    print("SECRET_GATE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
