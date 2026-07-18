# Plugin validator — SDK-only isolation for business plugins.

from __future__ import annotations

from pathlib import Path

from platform_architecture.rules import ROOT, ArchitectureViolation, ValidationSummary
from src.platform.layers.architecture_policy import is_plugin_module, scan_file, scan_layer


def validate_plugins(root: Path | None = None) -> ValidationSummary:
    root = root or ROOT
    violations_raw = scan_layer("plugins", root)
    violations = [
        ArchitectureViolation(
            category="plugin",
            rule=v.rule,
            path=v.path,
            detail=v.detail,
        )
        for v in violations_raw
    ]

    plugin_files = [
        path
        for path in root.rglob("*.py")
        if is_plugin_module(str(path.relative_to(root)).replace("\\", "/"))
    ]
    sdk_only_checks = 0
    sdk_only_passed = 0
    for path in plugin_files:
        rel = str(path.relative_to(root)).replace("\\", "/")
        sdk_only_checks += 1
        file_violations = scan_file(path, root=root)
        if not file_violations:
            sdk_only_passed += 1
        for item in file_violations:
            if item.rule == "plugin_sdk_only":
                violations.append(
                    ArchitectureViolation(
                        category="plugin",
                        rule="plugin_internal_import",
                        path=item.path,
                        detail=item.detail,
                    )
                )

    total_checks = max(len(plugin_files), 1)
    passed_checks = sdk_only_passed if plugin_files else 1
    return ValidationSummary(
        name="plugins",
        passed=not violations,
        total_checks=total_checks,
        passed_checks=passed_checks,
        violations=violations,
        metadata={"plugin_files": len(plugin_files)},
    )
