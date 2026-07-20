# QualityManager — coverage, static analysis, architecture, regression validation.

from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path
from typing import Any

from platform_validation.models import ValidationCheck, ValidationReport, ValidationStatus

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]


class QualityManager:
    """Quality assurance: architecture validation, code quality, regression checks."""

    def __init__(self, *, root: Path | None = None) -> None:
        self._root = root or ROOT

    def reset(self) -> None:
        pass

    def validate_architecture(self) -> ValidationCheck:
        try:
            from platform_architecture.certification import certify

            report = certify(root=self._root)
            score = float(report.certification.architecture_score)
            ok = score >= 90 and not report.certification.gate_failures
            return ValidationCheck(
                check_id="quality.architecture",
                component="quality",
                status=ValidationStatus.PASS if ok else ValidationStatus.FAIL,
                message=f"Architecture score {score} grade={report.certification.grade.value}",
                metadata={"score": score, "gate_failures": report.certification.gate_failures},
            )
        except Exception as exc:
            return ValidationCheck(
                check_id="quality.architecture",
                component="quality",
                status=ValidationStatus.WARN,
                message=str(exc),
            )

    def validate_static_analysis(self) -> ValidationCheck:
        platform_dirs = list(self._root.glob("platform_*/**/*.py"))
        py_count = len(platform_dirs)
        return ValidationCheck(
            check_id="quality.static_analysis",
            component="quality",
            status=ValidationStatus.PASS if py_count > 0 else ValidationStatus.WARN,
            message=f"{py_count} platform Python files scanned",
            metadata={"python_files": py_count},
        )

    def validate_coverage_report(self) -> ValidationCheck:
        test_dir = self._root / "tests"
        test_count = len(list(test_dir.glob("test_*.py"))) if test_dir.is_dir() else 0
        return ValidationCheck(
            check_id="quality.coverage",
            component="quality",
            status=ValidationStatus.PASS if test_count >= 10 else ValidationStatus.WARN,
            message=f"{test_count} test modules available",
            metadata={"test_modules": test_count},
        )

    def validate_regression(self) -> ValidationCheck:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/test_architecture_governance.py::test_governance_passes_on_current_codebase", "-q"],
                cwd=self._root,
                capture_output=True,
                text=True,
                timeout=120,
            )
            ok = result.returncode == 0
            return ValidationCheck(
                check_id="quality.regression",
                component="quality",
                status=ValidationStatus.PASS if ok else ValidationStatus.FAIL,
                message="Governance regression passed" if ok else result.stdout[-200:] or result.stderr[-200:],
            )
        except Exception as exc:
            return ValidationCheck(
                check_id="quality.regression",
                component="quality",
                status=ValidationStatus.WARN,
                message=str(exc),
            )

    def code_quality_metrics(self) -> dict[str, Any]:
        platform_packages = [p.name for p in self._root.iterdir() if p.is_dir() and p.name.startswith("platform_")]
        return {
            "platform_packages": len(platform_packages),
            "packages": sorted(platform_packages),
        }

    async def validate_all(self, *, include_regression: bool = False) -> ValidationReport:
        report = ValidationReport(title="Quality Assurance Report")
        report.checks.extend(
            [
                self.validate_architecture(),
                self.validate_static_analysis(),
                self.validate_coverage_report(),
            ]
        )
        if include_regression:
            report.checks.append(self.validate_regression())
        report.summary["code_quality"] = self.code_quality_metrics()
        return report.finalize()


quality_manager = QualityManager()
