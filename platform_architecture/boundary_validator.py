# Boundary validator — layered architecture enforcement.

from __future__ import annotations

from pathlib import Path

from platform_architecture.import_scanner import scan_all_imports, critical_import_violations
from platform_architecture.rules import (
    LEGACY_HANDLER_VIOLATIONS_ALLOWLIST,
    ROOT,
    ArchitectureViolation,
    ValidationSummary,
    ViolationSeverity,
)
from src.platform.layers.architecture_policy import scan_layer


def validate_boundaries(root: Path | None = None) -> ValidationSummary:
    root = root or ROOT
    all_violations = scan_all_imports(root)
    critical = critical_import_violations(all_violations)
    warnings = [v for v in all_violations if v.severity == ViolationSeverity.WARNING]

    management = scan_layer("management", root)
    plugins = scan_layer("plugins", root)

    checks = 3
    passed = 0
    if not management:
        passed += 1
    if not plugins:
        passed += 1
    if not critical:
        passed += 1

    return ValidationSummary(
        name="boundaries",
        passed=not critical,
        total_checks=checks,
        passed_checks=passed,
        violations=all_violations,
        metadata={
            "critical_count": len(critical),
            "warning_count": len(warnings),
            "allowlisted_handler_debt": len(LEGACY_HANDLER_VIOLATIONS_ALLOWLIST),
        },
    )


def filter_allowlisted(violations: list[ArchitectureViolation]) -> list[ArchitectureViolation]:
    return [v for v in violations if v.key() not in LEGACY_HANDLER_VIOLATIONS_ALLOWLIST]
