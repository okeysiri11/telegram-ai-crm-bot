# Session access policy — handlers must not open SQLAlchemy sessions directly.

from __future__ import annotations

import re
from pathlib import Path

HANDLER_SESSION_FORBIDDEN = (
    "Telegram/API handlers must not import get_session or open AsyncSession. "
    "Call a service method instead."
)

# Modules allowed to use get_session (everything else in handlers/routers is forbidden).
SESSION_ALLOWED_MODULES = frozenset({
    "services",
    "repositories",
    "database",
    "migrations",
    "scripts",
    "tests",
    "src/platform/layers",
    "src/domains",
    "src/verticals",
    "api",  # HTTP layer migrates to services incrementally
    "connectors",
    "startup",
    "bootstrap",
    "container",
})

_HANDLER_PATH_RE = re.compile(
    r"(^|/)(routers/|.*_handlers\.py$|handlers\.py$|middleware/)"
)


def is_handler_module(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return bool(_HANDLER_PATH_RE.search(normalized))


def assert_handler_session_policy(path: str, *, uses_get_session: bool) -> None:
    if uses_get_session and is_handler_module(path):
        raise RuntimeError(f"{HANDLER_SESSION_FORBIDDEN} Violation in {path}")


def scan_handler_session_violations(root: Path | None = None) -> list[str]:
    """Return handler file paths that import or call get_session."""
    root = root or Path(__file__).resolve().parents[3]
    violations: list[str] = []
    patterns = ("get_session", "AsyncSession")
    for rel in (
        "routers",
        "middleware",
        "handlers.py",
        "api/handlers.py",
    ):
        target = root / rel
        files: list[Path]
        if target.is_file():
            files = [target]
        elif target.is_dir():
            files = list(target.rglob("*.py"))
        else:
            continue
        for path in files:
            if not is_handler_module(str(path.relative_to(root))):
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            if any(p in text for p in patterns):
                violations.append(str(path.relative_to(root)))
    for path in root.glob("*_handlers.py"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "get_session" in text or "AsyncSession" in text:
            rel = str(path.relative_to(root))
            if rel not in violations:
                violations.append(rel)
    return sorted(violations)
