#!/usr/bin/env python3
"""Platform architecture protection gates — Sprint 38.4 baseline freeze.

Fails CI / pre-merge when unsafe patterns that previously broke the RC reappear:
empty modules, missing health/ready routes, missing migrations, dangerous
builtin shadowing, duplicate registry names, and (best-effort) critical import cycles.
"""

from __future__ import annotations

import ast
import builtins
import hashlib
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SHADOWABLE = {
    name
    for name in ("list", "dict", "set", "tuple", "type", "object", "id", "filter", "map", "input", "any", "all")
    if hasattr(builtins, name)
}

SCAN_DIRS = (
    "services",
    "repositories",
    "platform_security",
    "platform_jobs",
    "platform_sdk",
    "platform_orchestrator",
    "platform_workflow",
    "platform_enterprise_event_bus",
    "platform_management",
    "api",
    "database/models",
)

WORKFLOW_GLOBS = (
    "platform_workflow/**/*.yaml",
    "platform_workflow/**/*.yml",
    "platform_workflows/**/*.yaml",
    "platform_sdk/workflows/**/*.yaml",
)

CRITICAL_IMPORTS = (
    "api.server",
    "startup",
    "bot",
    "platform_security.audit.trail",
    "services.commission_engine",
)


def _iter_py(dirs: tuple[str, ...]):
    for rel in dirs:
        base = ROOT / rel
        if not base.exists():
            continue
        yield from base.rglob("*.py")


def _has_future_annotations(tree: ast.Module) -> bool:
    return any(
        isinstance(node, ast.ImportFrom)
        and node.module == "__future__"
        and any(alias.name == "annotations" for alias in node.names)
        for node in tree.body
    )


def _annotation_ids(class_node: ast.ClassDef) -> set[int]:
    roots: list[ast.AST] = []
    for node in ast.walk(class_node):
        if isinstance(node, ast.AnnAssign) and node.annotation is not None:
            roots.append(node.annotation)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.returns is not None:
                roots.append(node.returns)
            for arg in [
                *node.args.posonlyargs,
                *node.args.args,
                *node.args.kwonlyargs,
                node.args.vararg,
                node.args.kwarg,
            ]:
                if arg is not None and arg.annotation is not None:
                    roots.append(arg.annotation)
    return {id(child) for root in roots for child in ast.walk(root)}


def check_empty_python_modules() -> list[str]:
    bad = []
    for path in _iter_py(SCAN_DIRS):
        if path.stat().st_size == 0 and path.name != "__init__.py":
            bad.append(f"empty module: {path.relative_to(ROOT)}")
        # Empty non-init packages that used to brick imports (trail.py, ai_router.py)
        if path.stat().st_size == 0 and path.name in {"trail.py", "ai_router.py", "runtime_engine.py"}:
            bad.append(f"critical empty module: {path.relative_to(ROOT)}")
    return bad


def check_empty_init_allowed_but_critical_files() -> list[str]:
    """Explicit critical files must be non-empty even if named oddly."""
    required = [
        ROOT / "platform_security" / "audit" / "trail.py",
        ROOT / "services" / "ai_router.py",
        ROOT / "api" / "server.py",
        ROOT / "docker-entrypoint.sh",
        ROOT / "docker-compose.yml",
    ]
    bad = []
    for path in required:
        if not path.exists() or path.stat().st_size == 0:
            bad.append(f"missing/empty required file: {path.relative_to(ROOT)}")
    return bad


def check_builtin_shadowing() -> list[str]:
    bad = []
    for path in _iter_py(SCAN_DIRS):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            bad.append(f"syntax error: {path.relative_to(ROOT)} ({exc})")
            continue
        lazy = _has_future_annotations(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            defined = {
                item.name
                for item in node.body
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name in SHADOWABLE
            }
            if not defined:
                continue
            skip = _annotation_ids(node) if lazy else set()
            for inner in ast.walk(node):
                if (
                    isinstance(inner, ast.Subscript)
                    and isinstance(inner.value, ast.Name)
                    and inner.value.id in defined
                    and id(inner) not in skip
                ):
                    bad.append(
                        f"builtin shadowing: {path.relative_to(ROOT)} "
                        f"{node.name}.{inner.value.id}"
                    )
    return bad


def check_health_ready_routes() -> list[str]:
    server = ROOT / "api" / "server.py"
    text = server.read_text(encoding="utf-8") if server.exists() else ""
    bad = []
    if 'add_get("/health"' not in text and "add_get('/health'" not in text:
        bad.append("api/server.py missing /health route")
    if 'add_get("/ready"' not in text and "add_get('/ready'" not in text:
        bad.append("api/server.py missing /ready route")
    if 'add_get("/readiness"' not in text and "add_get('/readiness'" not in text:
        bad.append("api/server.py missing /readiness route")
    return bad


def check_alembic_migrations() -> list[str]:
    bad = []
    versions = ROOT / "migrations" / "versions"
    if not versions.is_dir():
        return ["migrations/versions directory missing"]
    py_files = [p for p in versions.glob("*.py") if p.name != "__init__.py"]
    if not py_files:
        bad.append("no Alembic migration modules under migrations/versions")
    head_hint = versions / "u4o567890123_version_mixin_full_backfill.py"
    if not head_hint.exists():
        # Soft: head may move; require at least one revision with down_revision chain
        if not any("revision" in p.read_text(encoding="utf-8", errors="ignore")[:500] for p in py_files[:5]):
            bad.append("migration files do not look like Alembic revisions")
    return bad


def check_empty_workflows() -> list[str]:
    bad = []
    for pattern in WORKFLOW_GLOBS:
        for path in ROOT.glob(pattern):
            if path.is_file() and path.stat().st_size == 0:
                bad.append(f"empty workflow file: {path.relative_to(ROOT)}")
    return bad


def check_duplicate_registry_names() -> list[str]:
    """Detect duplicate string literals registered as vertical/workflow/agent codes."""
    patterns = [
        (ROOT / "platform_sdk", re.compile(r"register(?:_vertical|_workflow)?\(\s*['\"]([a-z0-9_]+)['\"]")),
        (ROOT / "platform_workflow", re.compile(r"register\(\s*['\"]([a-z0-9_]+)['\"]")),
        (ROOT / "platform_orchestrator", re.compile(r"register(?:_agent)?\(\s*['\"]([A-Z0-9_]+)['\"]")),
    ]
    bad = []
    for base, rx in patterns:
        if not base.exists():
            continue
        seen: dict[str, list[str]] = defaultdict(list)
        for path in base.rglob("*.py"):
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            for match in rx.finditer(text):
                seen[match.group(1)].append(str(path.relative_to(ROOT)))
        for name, files in seen.items():
            uniq = sorted(set(files))
            if len(uniq) > 1 and len(files) > 1:
                # Same name registered from multiple files — flag
                if len(files) >= 2 and len(uniq) >= 2:
                    bad.append(f"duplicate registry name '{name}' in {', '.join(uniq[:4])}")
    return bad[:20]  # cap noise


def check_critical_imports() -> list[str]:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    bad = []
    for module in CRITICAL_IMPORTS:
        try:
            __import__(module)
        except Exception as exc:  # noqa: BLE001
            bad.append(f"critical import failed: {module} ({type(exc).__name__}: {exc})")
    return bad


def check_mass_rename_env() -> list[str]:
    """CI can set RENAMED_PATH_COUNT from the PR diff; block mass renames."""
    raw = os.environ.get("RENAMED_PATH_COUNT", "").strip()
    if not raw:
        return []
    try:
        count = int(raw)
    except ValueError:
        return [f"invalid RENAMED_PATH_COUNT={raw!r}"]
    if count >= 25 and os.environ.get("INFRASTRUCTURE_RENAME") != "1":
        return [
            f"mass rename detected ({count} paths). "
            "Set INFRASTRUCTURE_RENAME=1 only in an explicit infrastructure sprint."
        ]
    return []


def migration_checksums() -> dict[str, str]:
    versions = ROOT / "migrations" / "versions"
    out: dict[str, str] = {}
    if not versions.is_dir():
        return out
    for path in sorted(versions.glob("*.py")):
        if path.name == "__init__.py":
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        out[path.name] = digest
    return out


def main() -> int:
    checks = [
        ("empty_python_modules", check_empty_python_modules),
        ("required_files", check_empty_init_allowed_but_critical_files),
        ("builtin_shadowing", check_builtin_shadowing),
        ("health_ready_routes", check_health_ready_routes),
        ("alembic_migrations", check_alembic_migrations),
        ("empty_workflows", check_empty_workflows),
        ("duplicate_registry_names", check_duplicate_registry_names),
        ("critical_imports", check_critical_imports),
        ("mass_rename", check_mass_rename_env),
    ]
    failures: list[str] = []
    print("=== Platform protections (Sprint 38.4) ===")
    for name, fn in checks:
        issues = fn()
        if issues:
            print(f"[FAIL] {name}: {len(issues)}")
            for issue in issues:
                print(f"  - {issue}")
                failures.append(issue)
        else:
            print(f"[PASS] {name}")

    checksums = migration_checksums()
    print(f"[INFO] migration files checksummed: {len(checksums)}")
    head = "u4o567890123_version_mixin_full_backfill.py"
    if head in checksums:
        print(f"[INFO] alembic_head_file_sha256={checksums[head]}")

    if failures:
        print(f"\nPROTECTION_GATE=FAIL count={len(failures)}")
        return 1
    print("\nPROTECTION_GATE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
