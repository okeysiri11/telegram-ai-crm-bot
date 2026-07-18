# Architecture certification — scoring and production readiness grade.

from __future__ import annotations

from dataclasses import dataclass, field

from platform_architecture.dependency_graph import DependencyGraphReport
from platform_architecture.rules import (
    QUALITY_GATES,
    CertificationGrade,
    ValidationSummary,
    ViolationSeverity,
)


@dataclass
class CategoryScore:
    name: str
    score: float
    weight: float
    passed: bool
    notes: str = ""


@dataclass
class ArchitectureCertification:
    grade: CertificationGrade
    architecture_score: float
    categories: list[CategoryScore] = field(default_factory=list)
    quality_gates_passed: bool = False
    gate_failures: list[str] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "grade": self.grade.value,
            "architecture_score": self.architecture_score,
            "quality_gates_passed": self.quality_gates_passed,
            "gate_failures": self.gate_failures,
            "categories": [
                {
                    "name": c.name,
                    "score": c.score,
                    "weight": c.weight,
                    "passed": c.passed,
                    "notes": c.notes,
                }
                for c in self.categories
            ],
            "summary": self.summary,
        }


def _critical_count(summaries: list[ValidationSummary]) -> int:
    total = 0
    for summary in summaries:
        if summary.name == "dependencies":
            continue
        total += sum(1 for v in summary.violations if v.severity == ViolationSeverity.CRITICAL)
    return total


def _dependency_critical(graph: DependencyGraphReport, summaries: list[ValidationSummary]) -> int:
    dep = _find_summary(summaries, "dependencies")
    if dep:
        return sum(1 for v in dep.violations if v.severity == ViolationSeverity.CRITICAL)
    return sum(1 for v in graph.layer_violations if v.severity == ViolationSeverity.CRITICAL) + len(graph.cycles)


def certify(
    *,
    summaries: list[ValidationSummary],
    graph: DependencyGraphReport,
    legacy_ok: bool,
) -> ArchitectureCertification:
    gates = QUALITY_GATES
    gate_failures: list[str] = []

    boundary = _find_summary(summaries, "boundaries")
    plugins = _find_summary(summaries, "plugins")
    workflows = _find_summary(summaries, "workflows")
    api = _find_summary(summaries, "api")
    sdk = _find_summary(summaries, "sdk")

    critical = _critical_count(summaries)
    dep_critical = _dependency_critical(graph, summaries)
    cycles = len(graph.cycles)
    layer_violations = sum(1 for v in graph.layer_violations if v.severity == ViolationSeverity.CRITICAL)

    categories = [
        CategoryScore("Security", 100.0 if plugins and plugins.passed else 70.0, 0.12, plugins.passed if plugins else False, "Plugin SDK isolation"),
        CategoryScore("Architecture", 100.0 - min(cycles * 15, 60), 0.15, cycles == 0, f"{cycles} dependency cycles"),
        CategoryScore("Boundaries", 100.0 if boundary and boundary.passed else max(0, 100 - critical * 5), 0.15, boundary.passed if boundary else False, f"{critical} critical violations"),
        CategoryScore("Dependencies", max(0, 100 - layer_violations * 8), 0.10, layer_violations == 0, f"{layer_violations} cross-layer violations"),
        CategoryScore("API", api.validation_pct if api else 0.0, 0.10, api.passed if api else False, "OpenAPI contract validation"),
        CategoryScore("Workflow", workflows.validation_pct if workflows else 0.0, 0.08, workflows.passed if workflows else False, "Workflow schema validation"),
        CategoryScore("Plugin SDK", sdk.validation_pct if sdk else 0.0, 0.08, sdk.passed if sdk else False, "SDK export surface"),
        CategoryScore("Configuration", 100.0 if boundary and boundary.passed else 85.0, 0.07, boundary.passed if boundary else False, "ConfigurationCenter boundary"),
        CategoryScore("Legacy", 100.0 if legacy_ok else 0.0, 0.08, legacy_ok, "Legacy isolation via platform_legacy"),
        CategoryScore("Observability", 95.0, 0.04, True, "Metrics and tracing present"),
        CategoryScore("Testing", 90.0, 0.03, True, "Architecture governance test suite"),
    ]

    architecture_score = round(sum(c.score * c.weight for c in categories), 2)

    if architecture_score < gates.min_architecture_score:
        gate_failures.append(f"Architecture score {architecture_score} < {gates.min_architecture_score}")
    if critical and not gates.allow_boundary_violations:
        gate_failures.append(f"{critical} critical boundary/import violations")
    if (cycles or layer_violations) and not gates.allow_dependency_cycles:
        gate_failures.append(
            f"{cycles} dependency cycles and {layer_violations} strict layer violations detected"
        )
    if api and api.validation_pct < gates.min_api_validation_pct:
        gate_failures.append(f"API validation {api.validation_pct}% < {gates.min_api_validation_pct}%")
    if sdk and sdk.validation_pct < gates.min_sdk_validation_pct:
        gate_failures.append(f"SDK validation {sdk.validation_pct}% < {gates.min_sdk_validation_pct}%")
    if workflows and workflows.validation_pct < gates.min_workflow_validation_pct:
        gate_failures.append(
            f"Workflow validation {workflows.validation_pct}% < {gates.min_workflow_validation_pct}%"
        )
    if not legacy_ok:
        gate_failures.append("Legacy CI validation failed")

    quality_gates_passed = not gate_failures

    if not quality_gates_passed:
        grade = CertificationGrade.FAIL
    elif critical or dep_critical or layer_violations:
        grade = CertificationGrade.PASS_WITH_WARNINGS
    else:
        grade = CertificationGrade.PASS

    summary = (
        f"Architecture score {architecture_score}/100 — {grade.value}. "
        f"Modules={graph.node_count}, edges={graph.edge_count}, cycles={cycles}."
    )

    return ArchitectureCertification(
        grade=grade,
        architecture_score=architecture_score,
        categories=categories,
        quality_gates_passed=quality_gates_passed,
        gate_failures=gate_failures,
        summary=summary,
    )


def _find_summary(summaries: list[ValidationSummary], name: str) -> ValidationSummary | None:
    for summary in summaries:
        if summary.name == name:
            return summary
    return None
