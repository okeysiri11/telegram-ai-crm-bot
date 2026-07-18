# API validator — OpenAPI contracts, versioning, and response models.

from __future__ import annotations

from pathlib import Path

from platform_api.contracts import API_CONTRACT_VERSION, PLATFORM_API_VERSION
from platform_api.versioning import (
    MANAGEMENT_V1_PREFIX,
    PUBLIC_V1_PREFIX,
    build_management_openapi_spec,
    build_public_openapi_spec,
    reset_openapi_registry,
)
from platform_architecture.rules import ArchitectureViolation, ValidationSummary


def _validate_openapi_spec(
    spec: dict,
    *,
    prefix: str,
    name: str,
) -> list[ArchitectureViolation]:
    violations: list[ArchitectureViolation] = []
    checks = [
        ("openapi", spec.get("openapi", "").startswith("3.")),
        ("info.version", spec.get("info", {}).get("version") == API_CONTRACT_VERSION),
        ("components.schemas.ApiEnvelope", "ApiEnvelope" in spec.get("components", {}).get("schemas", {})),
    ]
    for check_name, ok in checks:
        if not ok:
            violations.append(
                ArchitectureViolation(
                    category="api",
                    rule=f"openapi_{check_name.replace('.', '_')}_invalid",
                    path=name,
                    detail=f"{check_name} check failed for {name}",
                )
            )

    paths = spec.get("paths", {})
    if not paths and name == "management":
        violations.append(
            ArchitectureViolation(
                category="api",
                rule="openapi_no_paths",
                path=name,
                detail="OpenAPI spec has no registered paths",
            )
        )

    strict_responses = prefix == MANAGEMENT_V1_PREFIX
    for path, methods in paths.items():
        if not path.startswith(prefix):
            violations.append(
                ArchitectureViolation(
                    category="api",
                    rule="openapi_unversioned_path",
                    path=path,
                    detail=f"path must start with {prefix}",
                )
            )
        for method, meta in methods.items():
            responses = meta.get("responses", {})
            if strict_responses and "200" not in responses and "201" not in responses:
                violations.append(
                    ArchitectureViolation(
                        category="api",
                        rule="openapi_missing_success_response",
                        path=f"{path}:{method}",
                        detail="missing 200/201 response contract",
                    )
                )
            if strict_responses:
                ref = (
                    responses.get("200", {})
                    .get("content", {})
                    .get("application/json", {})
                    .get("schema", {})
                    .get("$ref", "")
                )
                if ref and "ApiEnvelope" not in ref:
                    violations.append(
                        ArchitectureViolation(
                            category="api",
                            rule="openapi_missing_envelope",
                            path=f"{path}:{method}",
                            detail="management response must use ApiEnvelope",
                        )
                    )

    schemas = spec.get("components", {}).get("schemas", {})
    if "PaginationMeta" not in schemas and prefix == MANAGEMENT_V1_PREFIX:
        violations.append(
            ArchitectureViolation(
                category="api",
                rule="openapi_missing_pagination_schema",
                path=name,
                detail="PaginationMeta schema required",
            )
        )

    return violations


def validate_api(root: Path | None = None) -> ValidationSummary:
    del root
    from api.server import create_app

    reset_openapi_registry()
    create_app()

    violations: list[ArchitectureViolation] = []
    management_spec = build_management_openapi_spec()
    public_spec = build_public_openapi_spec()

    violations.extend(
        _validate_openapi_spec(management_spec, prefix=MANAGEMENT_V1_PREFIX, name="management")
    )
    violations.extend(
        _validate_openapi_spec(public_spec, prefix=PUBLIC_V1_PREFIX, name="public")
    )

    if PLATFORM_API_VERSION != "v1":
        violations.append(
            ArchitectureViolation(
                category="api",
                rule="api_version_mismatch",
                path="platform_api.contracts",
                detail=f"expected v1, got {PLATFORM_API_VERSION}",
            )
        )

    total_checks = 6
    passed_checks = total_checks - len({v.rule for v in violations})
    return ValidationSummary(
        name="api",
        passed=not violations,
        total_checks=total_checks,
        passed_checks=max(passed_checks, 0),
        violations=violations,
        metadata={
            "management_paths": len(management_spec.get("paths", {})),
            "public_paths": len(public_spec.get("paths", {})),
            "contract_version": API_CONTRACT_VERSION,
        },
    )
