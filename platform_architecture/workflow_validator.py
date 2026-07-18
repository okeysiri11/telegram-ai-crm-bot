# Workflow governance validator — schema, registry, and definition files.

from __future__ import annotations

from pathlib import Path

from platform_architecture.rules import (
    KNOWN_SERVICE_NAMES,
    ROOT,
    WORKFLOW_DEFINITIONS_DIR,
    ArchitectureViolation,
    ValidationSummary,
    ViolationSeverity,
)
from platform_workflows.models import StepType
from platform_workflows.workflow_loader import WorkflowLoader
from platform_workflows.workflow_validator import WorkflowValidator


def _validate_governance_step(workflow_id: str, step, *, source: str) -> list[ArchitectureViolation]:
    violations: list[ArchitectureViolation] = []
    prefix = f"{source}:{workflow_id}:{step.id}"

    if step.type == StepType.CALLBACK and not step.config.get("variable"):
        violations.append(
            ArchitectureViolation(
                category="workflow",
                rule="callback_missing_variable",
                path=prefix,
                detail="callback step requires variable binding",
            )
        )

    if step.type == StepType.SERVICE:
        service = step.config.get("service")
        if service and service not in KNOWN_SERVICE_NAMES:
            violations.append(
                ArchitectureViolation(
                    category="workflow",
                    rule="unknown_service_reference",
                    path=prefix,
                    detail=f"service {service} not in known registry",
                    severity=ViolationSeverity.WARNING,
                )
            )

    if step.retries < 0:
        violations.append(
            ArchitectureViolation(
                category="workflow",
                rule="invalid_retries",
                path=prefix,
                detail="retries must be >= 0",
            )
        )

    if step.timeout_seconds is not None and step.timeout_seconds <= 0:
        violations.append(
            ArchitectureViolation(
                category="workflow",
                rule="invalid_timeout",
                path=prefix,
                detail="timeout_seconds must be positive",
            )
        )

    return violations


def validate_workflows(
    root: Path | None = None,
    *,
    definitions_dir: Path | None = None,
) -> ValidationSummary:
    root = root or ROOT
    base = definitions_dir or WORKFLOW_DEFINITIONS_DIR
    violations: list[ArchitectureViolation] = []
    total = 0
    passed = 0

    if not base.exists():
        return ValidationSummary(
            name="workflows",
            passed=True,
            total_checks=0,
            passed_checks=0,
            violations=[],
            metadata={"definitions_dir": str(base), "workflow_count": 0},
        )

    for path in sorted(base.glob("*")):
        if path.suffix.lower() not in {".yaml", ".yml", ".json"}:
            continue
        total += 1
        rel = str(path.relative_to(root)).replace("\\", "/")
        try:
            definition = WorkflowLoader.load_file(path)
        except Exception as exc:
            violations.append(
                ArchitectureViolation(
                    category="workflow",
                    rule="workflow_load_failed",
                    path=rel,
                    detail=str(exc),
                )
            )
            continue

        structural_errors = WorkflowValidator.validate(definition)
        if structural_errors:
            for err in structural_errors:
                violations.append(
                    ArchitectureViolation(
                        category="workflow",
                        rule="workflow_schema_invalid",
                        path=f"{rel}:{definition.id}",
                        detail=err,
                    )
                )
            continue

        step_violations = []
        for step in definition.steps.values():
            step_violations.extend(
                _validate_governance_step(definition.id, step, source=rel)
            )
        critical_step = [v for v in step_violations if v.severity == ViolationSeverity.CRITICAL]
        violations.extend(step_violations)
        if not critical_step:
            passed += 1

    return ValidationSummary(
        name="workflows",
        passed=passed == total and not any(v.severity == ViolationSeverity.CRITICAL for v in violations),
        total_checks=total,
        passed_checks=passed,
        violations=violations,
        metadata={"definitions_dir": str(base), "workflow_count": total},
    )
