# Platform certification runner — Sprint 1.5.

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from platform_certification.checks import (
    check_api_repository_access,
    check_architecture_audit,
    check_canonical_event_bus,
    check_ci_enforcement,
    check_dependency_audit,
    check_documentation_sync,
    check_repository_service_imports,
    check_sdk_database_imports,
    check_sdk_repository_imports,
    check_security_tests,
    check_unauthorized_admin_routes,
    collect_metrics,
    run_pytest_suite,
)
from platform_certification.gates import CERTIFICATION_GATES_SPEC, CertificationGate, GateReport
from platform_certification.manifest import build_manifest, write_manifest
from platform_certification.reports import write_all_reports

ROOT = Path(__file__).resolve().parents[1]


@dataclass
class CertificationResult:
    verdict: str
    overall_score: float
    release_readiness: str
    gates: GateReport
    checks: list[dict[str, Any]] = field(default_factory=list)
    metrics: dict[str, object] = field(default_factory=dict)
    report_paths: list[Path] = field(default_factory=list)
    manifest_path: Path | None = None


class PlatformCertification:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or ROOT

    def run(self, *, write_reports: bool = True) -> CertificationResult:
        raw_checks = [
            check_repository_service_imports(),
            check_sdk_repository_imports(),
            check_sdk_database_imports(),
            check_api_repository_access(),
            check_unauthorized_admin_routes(),
            check_architecture_audit(),
            check_dependency_audit(),
            check_canonical_event_bus(),
            check_ci_enforcement(),
            check_documentation_sync(),
            check_security_tests(),
            run_pytest_suite(),
        ]
        checks = [
            {
                "check_id": c.check_id,
                "passed": c.passed,
                "message": c.message,
                "evidence": c.evidence,
                "metadata": c.metadata,
            }
            for c in raw_checks
        ]
        metrics = collect_metrics()
        gates = self._evaluate_gates(checks)
        health = self._health_scores(checks, metrics)
        overall = round(sum(health.values()) / len(health), 2)
        verdict = "PASS" if gates.passed else "FAIL"
        release = "PASS" if gates.passed else "NOT READY"

        certification = {
            "verdict": verdict,
            "overall_score": overall,
            "release_readiness": release,
            "gates_passed": gates.pass_count,
            "gates_total": len(gates.gates),
            "health_scores": health,
            "gates": [
                {"gate_id": g.gate_id, "description": g.description, "passed": g.passed, "evidence": g.evidence}
                for g in gates.gates
            ],
        }

        result = CertificationResult(
            verdict=verdict,
            overall_score=overall,
            release_readiness=release,
            gates=gates,
            checks=checks,
            metrics=metrics,
        )

        if write_reports:
            graph_summary = checks[[c["check_id"] for c in checks].index("dependency_audit")]["metadata"]
            result.report_paths = write_all_reports(
                checks=checks,
                metrics=metrics,
                certification=certification,
                graph_summary=graph_summary,
            )
            manifest_data = build_manifest(certification=certification, metrics=metrics, checks=checks)
            result.manifest_path = write_manifest(self.root / "platform_manifest.json", manifest_data)

        return result

    def _evaluate_gates(self, checks: list[dict[str, Any]]) -> GateReport:
        cm = {c["check_id"]: c for c in checks}
        gate_map = {
            "repository_service_imports": cm["repository_service_imports"]["passed"],
            "sdk_repository_imports": cm["sdk_repository_imports"]["passed"],
            "sdk_database_imports": cm["sdk_database_imports"]["passed"],
            "unauthorized_admin_api": cm["unauthorized_admin_api"]["passed"],
            "architecture_violations": cm["architecture_audit"]["passed"],
            "ci_enforcement": cm["ci_enforcement"]["passed"],
            "documentation_sync": cm["documentation_sync"]["passed"],
            "security_tests": cm["security_tests"]["passed"],
            "architecture_audit": cm["architecture_audit"]["passed"],
            "dependency_audit": cm["dependency_audit"]["passed"],
            "canonical_event_bus": cm["canonical_event_bus"]["passed"],
            "release_readiness": False,
        }
        report = GateReport()
        for gate_id, description in CERTIFICATION_GATES_SPEC:
            if gate_id == "release_readiness":
                continue
            passed = gate_map.get(gate_id, False)
            check = cm.get(gate_id, {})
            evidence = check.get("message", "")
            report.gates.append(
                CertificationGate(
                    gate_id=gate_id,
                    description=description,
                    passed=passed,
                    evidence=str(evidence),
                )
            )
        release_passed = all(g.passed for g in report.gates if g.severity == "critical")
        report.gates.append(
            CertificationGate(
                gate_id="release_readiness",
                description="Release readiness = PASS",
                passed=release_passed,
                evidence="All critical gates passed" if release_passed else "One or more critical gates failed",
            )
        )
        return report

    def _health_scores(self, checks: list[dict[str, Any]], metrics: dict[str, object]) -> dict[str, float]:
        cm = {c["check_id"]: c for c in checks}

        def score(check_id: str, *, pass_score: float = 100.0, fail_score: float = 35.0) -> float:
            return pass_score if cm.get(check_id, {}).get("passed") else fail_score

        return {
            "Architecture Health": min(score("architecture_audit"), score("repository_service_imports")),
            "Security Health": min(score("unauthorized_admin_api"), score("security_tests")),
            "Dependency Health": score("dependency_audit", fail_score=40.0),
            "Documentation Health": score("documentation_sync", fail_score=30.0),
            "CI Health": score("ci_enforcement", fail_score=20.0),
            "SDK Health": min(score("sdk_repository_imports"), score("sdk_database_imports")),
            "Event System Health": score("canonical_event_bus", fail_score=45.0),
        }

    def assert_certified(self) -> CertificationResult:
        result = self.run()
        if result.verdict == "PASS":
            return result
        failed = [g for g in result.gates.gates if not g.passed]
        lines = ["Platform certification FAILED:"]
        for gate in failed:
            lines.append(f"  - {gate.description}: {gate.evidence}")
        raise AssertionError("\n".join(lines))
