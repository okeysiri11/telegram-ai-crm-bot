# CI validation — fail build on legacy boundary violations.

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from platform_legacy.legacy_import_policy import (
    LEGACY_IMPORT_ALLOWLIST,
    scan_legacy_import_violations,
)

ROOT = Path(__file__).resolve().parents[1]

# Known legacy entrypoints — new matches fail CI.
_KNOWN_LEGACY_ROOT_FILES = frozenset({
    "handlers.py",
    "database_legacy.py",
    "openrouter.py",
    "platform_events_legacy.py",
})

_KNOWN_LEGACY_PREFIXES = (
    "services/pg_",
    "services/",
)


@dataclass(frozen=True, slots=True)
class CiValidationIssue:
    rule: str
    path: str
    detail: str

    def key(self) -> str:
        return f"{rule}|{path}|{detail}"


def scan_new_legacy_modules(root: Path | None = None) -> list[CiValidationIssue]:
    """Detect new top-level legacy modules not in baseline."""
    root = root or ROOT
    issues: list[CiValidationIssue] = []
    for name in _KNOWN_LEGACY_ROOT_FILES:
        path = root / name
        if not path.is_file():
            issues.append(
                CiValidationIssue(
                    "legacy_module_missing",
                    name,
                    "expected legacy module removed from baseline — update ci_validation baseline",
                )
            )
    for path in root.glob("services/pg_*.py"):
        rel = str(path.relative_to(root)).replace("\\", "/")
        if not rel.startswith("services/pg_"):
            issues.append(
                CiValidationIssue("new_legacy_module", rel, "unexpected legacy engine path")
            )
    return issues


def scan_direct_legacy_imports(root: Path | None = None) -> list[CiValidationIssue]:
    violations = scan_legacy_import_violations(root)
    platform_paths = (
        "platform_",
        "src/platform/",
        "src/verticals/",
        "startup.py",
        "events/",
    )
    issues: list[CiValidationIssue] = []
    for v in violations:
        if v.path.startswith("platform_legacy/"):
            continue
        if not any(v.path.startswith(p) for p in platform_paths):
            continue
        issues.append(
            CiValidationIssue(
                "direct_legacy_import",
                f"{v.path}:{v.line}",
                v.module,
            )
        )
    return issues


def scan_deprecated_without_adapter(root: Path | None = None) -> list[CiValidationIssue]:
    """Platform code importing deprecated modules must go through platform_legacy."""
    root = root or ROOT
    issues: list[CiValidationIssue] = []
    for issue in scan_direct_legacy_imports(root):
        if issue.path.split(":")[0] not in LEGACY_IMPORT_ALLOWLIST:
            issues.append(
                CiValidationIssue(
                    "deprecated_without_adapter",
                    issue.path,
                    f"import {issue.detail} must use platform_legacy compatibility layer",
                )
            )
    return issues


def validate_legacy_ci(root: Path | None = None) -> dict[str, Any]:
    root = root or ROOT
    import_issues = scan_direct_legacy_imports(root)
    adapter_issues = scan_deprecated_without_adapter(root)
    module_issues = scan_new_legacy_modules(root)
    all_issues = import_issues + adapter_issues + module_issues
    return {
        "ok": not all_issues,
        "issue_count": len(all_issues),
        "issues": [{"rule": i.rule, "path": i.path, "detail": i.detail} for i in all_issues],
    }


def assert_legacy_ci_clean(root: Path | None = None) -> None:
    result = validate_legacy_ci(root)
    if result["ok"]:
        return
    lines = ["Legacy CI validation failed:"]
    for item in result["issues"]:
        lines.append(f"  [{item['rule']}] {item['path']} — {item['detail']}")
    raise AssertionError("\n".join(lines))
