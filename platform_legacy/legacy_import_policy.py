# Legacy import policy — CI scanner for forbidden direct legacy imports.

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

_SKIP_DIRS = frozenset({".venv", "venv", "node_modules", "__pycache__", ".git", ".pytest_cache"})

# Only platform_legacy may import legacy subsystems directly.
LEGACY_IMPORT_ALLOWLIST: frozenset[str] = frozenset({
    "platform_legacy/adapter.py",
    "platform_legacy/__init__.py",
    "database/__init__.py",
})

# Legacy code itself (handlers, pg engines, etc.) is excluded from scans.
_LEGACY_CODE_PREFIXES = (
    "handlers.py",
    "database_legacy.py",
    "openrouter.py",
    "platform_events_legacy.py",
    "services/pg_",
    "services/",
    "api/handlers.py",
    "routers/",
    "middleware/",
    "migrations/",
    "scripts/",
    "tests/",
)

_FORBIDDEN_MODULE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^handlers$"),
    re.compile(r"^database_legacy(?:\.|$)"),
    re.compile(r"^openrouter(?:\.|$)"),
    re.compile(r"^services\.pg_"),
)


@dataclass(frozen=True, slots=True)
class LegacyImportViolation:
    path: str
    line: int
    module: str

    def key(self) -> str:
        return f"{self.path}:{self.line}:{self.module}"


def _is_legacy_code_file(rel: str) -> bool:
    normalized = rel.replace("\\", "/")
    if normalized in {"handlers.py", "database_legacy.py", "openrouter.py", "platform_events_legacy.py"}:
        return True
    for prefix in _LEGACY_CODE_PREFIXES:
        if normalized.startswith(prefix) or normalized.endswith(prefix):
            if prefix.endswith(".py") and normalized == prefix:
                return True
            if prefix.endswith("/") and normalized.startswith(prefix):
                return True
    if normalized.endswith("_handlers.py"):
        return True
    if "/services/pg_" in f"/{normalized}" or normalized.startswith("services/pg_"):
        return True
    return False


def _is_allowlisted(rel: str) -> bool:
    normalized = rel.replace("\\", "/")
    if normalized in LEGACY_IMPORT_ALLOWLIST:
        return True
    if normalized.startswith("platform_legacy/"):
        return True
    return False


def _module_imports(path: Path) -> list[tuple[int, str]]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except SyntaxError:
        return []
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.append((node.lineno, alias.name))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                found.append((node.lineno, node.module))
    return found


def _is_forbidden(module: str) -> bool:
    for pattern in _FORBIDDEN_MODULE_PATTERNS:
        if pattern.search(module):
            return True
    return False


def scan_legacy_import_violations(root: Path | None = None) -> list[LegacyImportViolation]:
    root = root or ROOT
    violations: list[LegacyImportViolation] = []
    for path in root.rglob("*.py"):
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        rel = str(path.relative_to(root)).replace("\\", "/")
        if _is_allowlisted(rel) or _is_legacy_code_file(rel):
            continue
        for line_no, module in _module_imports(path):
            if _is_forbidden(module):
                violations.append(
                    LegacyImportViolation(path=rel, line=line_no, module=module)
                )
    return sorted(violations, key=lambda v: (v.path, v.line, v.module))
