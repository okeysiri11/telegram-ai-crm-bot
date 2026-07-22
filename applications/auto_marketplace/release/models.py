# Production release models — Sprint 6.8.

from __future__ import annotations

import enum
import time
from dataclasses import dataclass, field
from typing import Any


def _ts() -> float:
    return time.time()


class ValidationStatus(str, enum.Enum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


@dataclass
class ValidationResult:
    check_id: str = ""
    category: str = ""
    name: str = ""
    status: ValidationStatus = ValidationStatus.PASSED
    message: str = ""
    duration_ms: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "category": self.category,
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "duration_ms": self.duration_ms,
            "details": dict(self.details),
        }


@dataclass
class PerformanceBenchmark:
    name: str = ""
    operations: int = 0
    total_ms: float = 0.0
    avg_ms: float = 0.0
    p95_ms: float = 0.0
    passed: bool = True
    threshold_ms: float = 100.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "operations": self.operations,
            "total_ms": round(self.total_ms, 2),
            "avg_ms": round(self.avg_ms, 2),
            "p95_ms": round(self.p95_ms, 2),
            "passed": self.passed,
            "threshold_ms": self.threshold_ms,
        }


@dataclass
class ReleaseReport:
    application_version: str = "2.0.0"
    release_status: str = "Commercial Release"
    platform_dependency: str = "AI Platform Core v3"
    validations: list[ValidationResult] = field(default_factory=list)
    benchmarks: list[PerformanceBenchmark] = field(default_factory=list)
    security_audit: list[ValidationResult] = field(default_factory=list)
    production_ready: bool = False
    generated_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        passed = sum(1 for v in self.validations if v.status == ValidationStatus.PASSED)
        return {
            "application_version": self.application_version,
            "release_status": self.release_status,
            "platform_dependency": self.platform_dependency,
            "production_ready": self.production_ready,
            "validations_passed": passed,
            "validations_total": len(self.validations),
            "benchmarks": [b.to_dict() for b in self.benchmarks],
            "validations": [v.to_dict() for v in self.validations],
            "security_audit": [s.to_dict() for s in self.security_audit],
            "generated_at": self.generated_at,
        }
