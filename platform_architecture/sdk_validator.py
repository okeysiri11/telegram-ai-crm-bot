# SDK validator — public export surface and forbidden internal imports.

from __future__ import annotations

import ast
from pathlib import Path

from platform_architecture.rules import (
    ROOT,
    SDK_FORBIDDEN_PREFIXES,
    ArchitectureViolation,
    ValidationSummary,
    ViolationSeverity,
)


def _matches_prefix(module: str, prefixes: tuple[str, ...]) -> bool:
    for prefix in prefixes:
        if module == prefix or module.startswith(f"{prefix}."):
            return True
    return False


def _collect_defined_public_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.add(alias.asname or alias.name.split(".")[-1])
        elif isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.asname or alias.name.split(".")[-1])
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not node.name.startswith("_"):
                names.add(node.name)
    return names


def validate_sdk(root: Path | None = None) -> ValidationSummary:
    root = root or ROOT
    sdk_root = root / "platform_plugin_sdk"
    init_path = sdk_root / "__init__.py"
    violations: list[ArchitectureViolation] = []

    if not init_path.is_file():
        return ValidationSummary(
            name="sdk",
            passed=False,
            total_checks=1,
            passed_checks=0,
            violations=[
                ArchitectureViolation(
                    category="sdk",
                    rule="sdk_missing",
                    path=str(init_path),
                    detail="platform_plugin_sdk/__init__.py not found",
                )
            ],
        )

    init_tree = ast.parse(init_path.read_text(encoding="utf-8", errors="ignore"))
    declared_all: list[str] = []
    for node in init_tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__" and isinstance(node.value, ast.List):
                    declared_all = [
                        elt.value for elt in node.value.elts if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                    ]

    if not declared_all:
        violations.append(
            ArchitectureViolation(
                category="sdk",
                rule="sdk_missing_all",
                path="platform_plugin_sdk/__init__.py",
                detail="__all__ must declare public exports",
            )
        )

    defined = _collect_defined_public_names(init_path)
    for name in declared_all:
        if name.startswith("_"):
            violations.append(
                ArchitectureViolation(
                    category="sdk",
                    rule="sdk_private_export",
                    path="platform_plugin_sdk/__init__.py",
                    detail=f"private symbol exported: {name}",
                )
            )
        if name not in defined and name not in {"SDK_VERSION"}:
            violations.append(
                ArchitectureViolation(
                    category="sdk",
                    rule="sdk_undefined_export",
                    path="platform_plugin_sdk/__init__.py",
                    detail=f"exported symbol not defined in __init__: {name}",
                    severity=ViolationSeverity.WARNING,
                )
            )

    sdk_files = list(sdk_root.rglob("*.py"))
    forbidden_checks = 0
    forbidden_passed = 0
    for path in sdk_files:
        rel = str(path.relative_to(root)).replace("\\", "/")
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        for node in ast.walk(tree):
            modules: list[str] = []
            if isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.append(node.module)
            for module in modules:
                forbidden_checks += 1
                if _matches_prefix(module, SDK_FORBIDDEN_PREFIXES):
                    violations.append(
                        ArchitectureViolation(
                            category="sdk",
                            rule="sdk_forbidden_import",
                            path=rel,
                            detail=f"imports {module}",
                        )
                    )
                else:
                    forbidden_passed += 1

    total_checks = max(len(declared_all), 1) + max(forbidden_checks, 1)
    passed_checks = (len(declared_all) if declared_all and not violations else 0) + forbidden_passed
    return ValidationSummary(
        name="sdk",
        passed=not violations,
        total_checks=total_checks,
        passed_checks=min(passed_checks, total_checks),
        violations=violations,
        metadata={"declared_exports": declared_all, "sdk_files": len(sdk_files)},
    )
