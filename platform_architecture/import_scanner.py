# Import scanner — forbidden import detection across architectural zones.

from __future__ import annotations

import ast
import re
from pathlib import Path

from platform_architecture.rules import (
    FORBIDDEN_IMPORT_PREFIXES,
    LEGACY_FORBIDDEN_PLATFORM_PREFIXES,
    LEGACY_HANDLER_VIOLATIONS_ALLOWLIST,
    LEGACY_PUBLIC_PREFIXES,
    ROOT,
    SKIP_DIRS,
    ArchitectureViolation,
    ViolationSeverity,
)
from platform_configuration.env_access_policy import scan_env_access_violations
from platform_legacy.legacy_import_policy import scan_legacy_import_violations
from src.platform.layers.architecture_policy import (
    BoundaryViolation,
    iter_python_files,
    scan_architecture_violations,
)


def _matches_prefix(module: str, prefixes: tuple[str, ...]) -> bool:
    for prefix in prefixes:
        if module == prefix or module.startswith(f"{prefix}."):
            return True
    return False


def _module_imports(path: Path) -> list[tuple[int, str]]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except SyntaxError:
        return []
    imports: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append((node.lineno, alias.name))
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append((node.lineno, node.module))
    return imports


def _zone_for_path(rel: str) -> str | None:
    normalized = rel.replace("\\", "/")
    for zone in FORBIDDEN_IMPORT_PREFIXES:
        if zone.endswith(".py"):
            if normalized == zone:
                return zone
        elif normalized.startswith(zone):
            return zone
    if _is_legacy_code_file(normalized):
        return "legacy"
    return None


def _is_legacy_code_file(normalized: str) -> bool:
    legacy_roots = {
        "handlers.py",
        "database_legacy.py",
        "openrouter.py",
        "platform_events_legacy.py",
    }
    if normalized in legacy_roots:
        return True
    if normalized.startswith("services/pg_"):
        return True
    if normalized.endswith("_handlers.py") and not normalized.startswith("events/handlers/"):
        return True
    return False


def _boundary_to_violation(item: BoundaryViolation) -> ArchitectureViolation:
    key = item.key()
    severity = ViolationSeverity.WARNING if key in LEGACY_HANDLER_VIOLATIONS_ALLOWLIST else ViolationSeverity.CRITICAL
    return ArchitectureViolation(
        category="boundary",
        rule=item.rule,
        path=item.path,
        detail=item.detail,
        severity=severity,
    )


def scan_zone_imports(root: Path | None = None) -> list[ArchitectureViolation]:
    root = root or ROOT
    violations: list[ArchitectureViolation] = []

    for path in iter_python_files(root):
        rel = str(path.relative_to(root)).replace("\\", "/")
        zone = _zone_for_path(rel)
        if zone is None:
            continue

        if zone == "legacy":
            for line_no, module in _module_imports(path):
                if _matches_prefix(module, LEGACY_PUBLIC_PREFIXES):
                    continue
                module_root = module.split(".", 1)[0]
                if module_root != "platform_":
                    continue
                if _matches_prefix(module, LEGACY_FORBIDDEN_PLATFORM_PREFIXES):
                    violations.append(
                        ArchitectureViolation(
                            category="import",
                            rule="legacy_no_platform_core",
                            path=f"{rel}:{line_no}",
                            detail=f"legacy imports {module}",
                        )
                    )
            continue

        forbidden = FORBIDDEN_IMPORT_PREFIXES.get(zone, ())
        for line_no, module in _module_imports(path):
            if _matches_prefix(module, forbidden):
                violations.append(
                    ArchitectureViolation(
                        category="import",
                        rule=f"{zone.replace('/', '_')}_forbidden_import",
                        path=f"{rel}:{line_no}",
                        detail=f"imports {module}",
                    )
                )
    return sorted(violations, key=lambda v: (v.rule, v.path, v.detail))


def scan_env_imports(root: Path | None = None) -> list[ArchitectureViolation]:
    root = root or ROOT
    return [
        ArchitectureViolation(
            category="configuration",
            rule="env_access_outside_center",
            path=f"{v.path}:{v.line}",
            detail=v.detail,
        )
        for v in scan_env_access_violations(root)
    ]


def scan_legacy_imports(root: Path | None = None) -> list[ArchitectureViolation]:
    root = root or ROOT
    platform_prefixes = ("platform_", "src/platform/", "src/verticals/", "startup.py", "events/")
    violations: list[ArchitectureViolation] = []
    for item in scan_legacy_import_violations(root):
        if item.path.startswith("platform_legacy/"):
            continue
        if not any(item.path.startswith(prefix) for prefix in platform_prefixes):
            continue
        violations.append(
            ArchitectureViolation(
                category="legacy",
                rule="direct_legacy_import",
                path=f"{item.path}:{item.line}",
                detail=item.module,
            )
        )
    return violations


def scan_all_imports(root: Path | None = None) -> list[ArchitectureViolation]:
    root = root or ROOT
    violations: list[ArchitectureViolation] = []
    violations.extend(_boundary_to_violation(v) for v in scan_architecture_violations(root))
    violations.extend(scan_zone_imports(root))
    violations.extend(scan_env_imports(root))
    violations.extend(scan_legacy_imports(root))
    return sorted(violations, key=lambda v: (v.category, v.rule, v.path, v.detail))


def critical_import_violations(violations: list[ArchitectureViolation]) -> list[ArchitectureViolation]:
    return [v for v in violations if v.severity == ViolationSeverity.CRITICAL]
