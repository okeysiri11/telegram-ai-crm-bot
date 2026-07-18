# Environment access policy — only ConfigurationCenter may read os.environ / dotenv.

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

_ENV_ACCESS_PATTERNS = (
    re.compile(r"\bos\.getenv\s*\("),
    re.compile(r"\bos\.environ\s*\["),
    re.compile(r"\bos\.environ\.get\s*\("),
    re.compile(r"\bload_dotenv\s*\("),
)

_SKIP_DIRS = frozenset({".venv", "venv", "node_modules", "__pycache__", ".git", ".pytest_cache"})

# Paths allowed to touch environment variables directly.
ENV_ACCESS_ALLOWLIST: frozenset[str] = frozenset({
    "platform_configuration/env_source.py",
    "migrations/env.py",
})


@dataclass(frozen=True, slots=True)
class EnvAccessViolation:
    path: str
    line: int
    detail: str

    def key(self) -> str:
        return f"{self.path}:{self.line}:{self.detail}"


def _is_allowlisted(rel: str) -> bool:
    normalized = rel.replace("\\", "/")
    if normalized in ENV_ACCESS_ALLOWLIST:
        return True
    if normalized.startswith("tests/"):
        return True
    if normalized.startswith("scripts/"):
        return True
    return False


def scan_env_access_violations(root: Path | None = None) -> list[EnvAccessViolation]:
    root = root or ROOT
    violations: list[EnvAccessViolation] = []
    for path in root.rglob("*.py"):
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        rel = str(path.relative_to(root)).replace("\\", "/")
        if _is_allowlisted(rel):
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for line_no, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            for pattern in _ENV_ACCESS_PATTERNS:
                if pattern.search(line):
                    violations.append(
                        EnvAccessViolation(
                            path=rel,
                            line=line_no,
                            detail=pattern.pattern,
                        )
                    )
                    break
    return sorted(violations, key=lambda v: (v.path, v.line, v.detail))
