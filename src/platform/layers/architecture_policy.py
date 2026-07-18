# Architecture boundary policy — static import analysis for layered design.
#
# Rules enforced:
#   Management → Services → Repositories → PostgreSQL
#   Never: Management → DB
#   Never: Handler → Repository
#   Never: Plugin → Repository / PostgreSQL / AI Provider
#   Only:  Plugin → SDK → Platform APIs

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[3]

# stdlib roots allowed in plugins without counting as violations
_STDLIB_ROOTS = frozenset({
    "__future__",
    "abc",
    "asyncio",
    "collections",
    "contextlib",
    "copy",
    "dataclasses",
    "datetime",
    "decimal",
    "enum",
    "functools",
    "hashlib",
    "importlib",
    "io",
    "itertools",
    "json",
    "logging",
    "math",
    "operator",
    "os",
    "pathlib",
    "re",
    "secrets",
    "string",
    "sys",
    "time",
    "traceback",
    "types",
    "typing",
    "uuid",
    "warnings",
})

_DB_PREFIXES = ("database", "database_legacy", "sqlalchemy", "asyncpg")
_REPO_PREFIXES = ("repositories",)
_AI_PROVIDER_PREFIXES = (
    "openai",
    "anthropic",
    "openrouter",
    "platform_ai.providers",
    "platform_ai.llm",
    "platform_ai.ai_providers",
)

_HANDLER_PATH_RE = re.compile(
    r"(^|/)(events/handlers/|.*_handlers\.py$|handlers\.py$|routers/|api/handlers\.py$|middleware/)"
)


@dataclass(frozen=True, slots=True)
class BoundaryViolation:
    rule: str
    path: str
    detail: str

    def key(self) -> str:
        return f"{self.rule}|{self.path}|{self.detail}"


def _module_imports(path: Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except SyntaxError:
        return []
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.append(node.module)
    return modules


def _matches_prefix(module: str, prefixes: tuple[str, ...]) -> bool:
    for prefix in prefixes:
        if module == prefix or module.startswith(f"{prefix}."):
            return True
    return False


def is_handler_module(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return bool(_HANDLER_PATH_RE.search(normalized))


def is_management_module(path: str) -> bool:
    return path.replace("\\", "/").startswith("platform_management/")


def is_plugin_module(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized.startswith("plugins/") and not normalized.endswith("plugins/_scaffold.py")


def _is_plugin_allowed_import(module: str) -> bool:
    root = module.split(".", 1)[0]
    if root in _STDLIB_ROOTS:
        return True
    if module == "platform_plugin_sdk" or module.startswith("platform_plugin_sdk."):
        return True
    if module == "aiohttp" or module.startswith("aiohttp."):
        return True
    return False


def scan_file(path: Path, *, root: Path | None = None) -> list[BoundaryViolation]:
    root = root or ROOT
    rel = str(path.relative_to(root)).replace("\\", "/")
    imports = _module_imports(path)
    violations: list[BoundaryViolation] = []

    has_db = any(_matches_prefix(m, _DB_PREFIXES) for m in imports)
    has_repo = any(_matches_prefix(m, _REPO_PREFIXES) for m in imports)
    has_ai_provider = any(_matches_prefix(m, _AI_PROVIDER_PREFIXES) for m in imports)
    has_platform_ai = any(m == "platform_ai" or m.startswith("platform_ai.") for m in imports)

    if is_management_module(rel):
        if has_db:
            violations.append(
                BoundaryViolation("management_no_database", rel, "imports database/sqlalchemy layer")
            )
        if has_repo:
            violations.append(
                BoundaryViolation("management_no_repository", rel, "imports repositories layer")
            )

    if is_handler_module(rel):
        if has_repo:
            violations.append(
                BoundaryViolation("handler_no_repository", rel, "imports repositories layer")
            )
        if has_db:
            # database.models enums/constants are still a DB-layer leak; handlers use services.
            violations.append(
                BoundaryViolation("handler_no_database", rel, "imports database layer")
            )

    if is_plugin_module(rel):
        for module in imports:
            if _is_plugin_allowed_import(module):
                continue
            if _matches_prefix(module, _REPO_PREFIXES):
                violations.append(
                    BoundaryViolation("plugin_no_repository", rel, f"imports {module}")
                )
            elif _matches_prefix(module, _DB_PREFIXES):
                violations.append(
                    BoundaryViolation("plugin_no_database", rel, f"imports {module}")
                )
            elif _matches_prefix(module, _AI_PROVIDER_PREFIXES) or (
                has_platform_ai and module.startswith("platform_ai")
            ):
                violations.append(
                    BoundaryViolation("plugin_no_ai_provider", rel, f"imports {module}")
                )
            elif not module.startswith("platform_plugin_sdk"):
                violations.append(
                    BoundaryViolation("plugin_sdk_only", rel, f"imports {module}")
                )

    return violations


def iter_python_files(root: Path | None = None) -> Iterable[Path]:
    root = root or ROOT
    skip = {".venv", "node_modules", "__pycache__", ".git", ".pytest_cache"}
    for path in root.rglob("*.py"):
        if any(part in skip for part in path.parts):
            continue
        yield path


def scan_architecture_violations(
    root: Path | None = None,
    *,
    include_paths: Iterable[str] | None = None,
) -> list[BoundaryViolation]:
    root = root or ROOT
    violations: list[BoundaryViolation] = []
    for path in iter_python_files(root):
        rel = str(path.relative_to(root)).replace("\\", "/")
        if include_paths is not None and rel not in include_paths:
            continue
        violations.extend(scan_file(path, root=root))
    return sorted(violations, key=lambda v: (v.rule, v.path, v.detail))


def scan_layer(
    layer: str,
    root: Path | None = None,
) -> list[BoundaryViolation]:
    """Scan a named layer prefix: management, handlers, plugins."""
    root = root or ROOT
    prefixes = {
        "management": ("platform_management/",),
        "handlers": None,  # use is_handler_module
        "plugins": ("plugins/",),
    }
    if layer not in prefixes:
        raise ValueError(f"Unknown layer: {layer}")

    violations: list[BoundaryViolation] = []
    for path in iter_python_files(root):
        rel = str(path.relative_to(root)).replace("\\", "/")
        if layer == "management" and not rel.startswith("platform_management/"):
            continue
        if layer == "handlers" and not is_handler_module(rel):
            continue
        if layer == "plugins" and not is_plugin_module(rel):
            continue
        violations.extend(scan_file(path, root=root))
    return sorted(violations, key=lambda v: (v.rule, v.path, v.detail))
