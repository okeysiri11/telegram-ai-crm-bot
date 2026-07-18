# Architecture governance — orchestrates all validators and quality gates.

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from platform_architecture.api_validator import validate_api
from platform_architecture.boundary_validator import validate_boundaries
from platform_architecture.certification import ArchitectureCertification, certify
from platform_architecture.dependency_graph import build_dependency_graph, graph_violations
from platform_architecture.plugin_validator import validate_plugins
from platform_architecture.report_generator import (
    generate_architecture_certificate,
    generate_architecture_report,
)
from platform_architecture.rules import (
    ROOT,
    ArchitectureViolation,
    CertificationGrade,
    ValidationSummary,
    ViolationSeverity,
)
from platform_architecture.sdk_validator import validate_sdk
from platform_architecture.workflow_validator import validate_workflows
from platform_legacy.ci_validation import validate_legacy_ci


@dataclass
class GovernanceReport:
    passed: bool
    certification: ArchitectureCertification
    summaries: list[ValidationSummary] = field(default_factory=list)
    graph_violations: list[ArchitectureViolation] = field(default_factory=list)
    report_path: Path | None = None
    certificate_path: Path | None = None

    @property
    def critical_violations(self) -> list[ArchitectureViolation]:
        items: list[ArchitectureViolation] = []
        for summary in self.summaries:
            items.extend(v for v in summary.violations if v.severity == ViolationSeverity.CRITICAL)
        items.extend(v for v in self.graph_violations if v.severity == ViolationSeverity.CRITICAL)
        return items


class ArchitectureGovernance:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or ROOT

    def run_all(
        self,
        *,
        write_reports: bool = True,
        report_path: Path | None = None,
        certificate_path: Path | None = None,
    ) -> GovernanceReport:
        summaries = [
            validate_boundaries(self.root),
            validate_plugins(self.root),
            validate_workflows(self.root),
            validate_api(self.root),
            validate_sdk(self.root),
        ]

        graph = build_dependency_graph(self.root)
        graph_issues = graph_violations(graph)
        dependency_summary = ValidationSummary(
            name="dependencies",
            passed=not any(v.severity == ViolationSeverity.CRITICAL for v in graph_issues),
            total_checks=max(graph.edge_count, 1),
            passed_checks=graph.edge_count - len(graph.layer_violations) - len(graph.cycles),
            violations=graph_issues,
            metadata={
                "nodes": graph.node_count,
                "edges": graph.edge_count,
                "cycles": len(graph.cycles),
            },
        )
        summaries.append(dependency_summary)

        legacy_result = validate_legacy_ci(self.root)
        legacy_summary = ValidationSummary(
            name="legacy",
            passed=legacy_result["ok"],
            total_checks=1,
            passed_checks=1 if legacy_result["ok"] else 0,
            violations=[
                ArchitectureViolation(
                    category="legacy",
                    rule=item["rule"],
                    path=item["path"],
                    detail=item["detail"],
                )
                for item in legacy_result["issues"]
            ],
            metadata={"issue_count": legacy_result["issue_count"]},
        )
        summaries.append(legacy_summary)

        certification = certify(
            summaries=summaries,
            graph=graph,
            legacy_ok=legacy_result["ok"],
        )

        report_file: Path | None = None
        cert_file: Path | None = None
        if write_reports:
            report_file = generate_architecture_report(
                summaries=summaries,
                graph=graph,
                certification=certification,
                output_path=report_path,
            )
            cert_file = generate_architecture_certificate(
                certification,
                output_path=certificate_path,
            )

        passed = certification.quality_gates_passed and certification.grade != CertificationGrade.FAIL
        return GovernanceReport(
            passed=passed,
            certification=certification,
            summaries=summaries,
            graph_violations=graph_issues,
            report_path=report_file,
            certificate_path=cert_file,
        )

    def assert_clean(self) -> GovernanceReport:
        report = self.run_all()
        if report.passed:
            return report
        lines = ["Architecture governance failed:"]
        for failure in report.certification.gate_failures:
            lines.append(f"  - {failure}")
        for violation in report.critical_violations[:20]:
            lines.append(f"  - [{violation.category}/{violation.rule}] {violation.path}: {violation.detail}")
        raise AssertionError("\n".join(lines))
