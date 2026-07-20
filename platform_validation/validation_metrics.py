# Validation metrics.

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from platform_validation.models import CertificationResult, ValidationReport, ValidationStatus


@dataclass
class ValidationMetrics:
    validation_runs: int = 0
    validation_duration_ms: float = 0.0
    checks_passed: int = 0
    checks_failed: int = 0
    checks_warned: int = 0
    certification_runs: int = 0
    certification_success_rate: float = 0.0
    last_certified: bool = False
    reports: dict[str, str] = field(default_factory=dict)

    def reset(self) -> None:
        self.validation_runs = 0
        self.validation_duration_ms = 0.0
        self.checks_passed = 0
        self.checks_failed = 0
        self.checks_warned = 0
        self.certification_runs = 0
        self.certification_success_rate = 0.0
        self.last_certified = False
        self.reports.clear()

    def record_validation(self, report: ValidationReport, duration_ms: float) -> None:
        self.validation_runs += 1
        self.validation_duration_ms += duration_ms
        for check in report.checks:
            if check.status == ValidationStatus.PASS:
                self.checks_passed += 1
            elif check.status == ValidationStatus.FAIL:
                self.checks_failed += 1
            elif check.status == ValidationStatus.WARN:
                self.checks_warned += 1
        self.reports[report.title] = report.status.value

    def record_certification(self, result: CertificationResult) -> None:
        self.certification_runs += 1
        self.last_certified = result.certified
        if self.certification_runs:
            successes = sum(1 for _ in range(self.certification_runs) if self.last_certified)
            self.certification_success_rate = successes / self.certification_runs

    def summary(self) -> dict[str, Any]:
        avg_duration = (
            self.validation_duration_ms / self.validation_runs if self.validation_runs else 0.0
        )
        total_checks = self.checks_passed + self.checks_failed + self.checks_warned
        pass_rate = self.checks_passed / total_checks if total_checks else 0.0
        return {
            "validation_runs": self.validation_runs,
            "validation_duration_avg_ms": round(avg_duration, 2),
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
            "checks_warned": self.checks_warned,
            "pass_rate": round(pass_rate, 4),
            "certification_runs": self.certification_runs,
            "last_certified": self.last_certified,
            "reports": dict(self.reports),
            "recorded_at": time.time(),
        }


validation_metrics = ValidationMetrics()
