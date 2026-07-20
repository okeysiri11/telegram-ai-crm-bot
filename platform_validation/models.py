# Platform Validation & Production Readiness — core models.

from __future__ import annotations

import enum
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


class ValidationStatus(str, enum.Enum):
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"
    SKIP = "skip"


class ReadinessLevel(str, enum.Enum):
    NOT_READY = "not_ready"
    PARTIAL = "partial"
    PRODUCTION_READY = "production_ready"


@dataclass
class ValidationCheck:
    check_id: str
    component: str
    status: ValidationStatus
    message: str
    duration_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "component": self.component,
            "status": self.status.value,
            "message": self.message,
            "duration_ms": round(self.duration_ms, 2),
            "metadata": dict(self.metadata),
        }


@dataclass
class ValidationReport:
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "Platform Validation Report"
    status: ValidationStatus = ValidationStatus.PASS
    checks: list[ValidationCheck] = field(default_factory=list)
    started_at: float = field(default_factory=time.time)
    completed_at: float | None = None
    duration_ms: float = 0.0
    summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        passed = sum(1 for c in self.checks if c.status == ValidationStatus.PASS)
        failed = sum(1 for c in self.checks if c.status == ValidationStatus.FAIL)
        warned = sum(1 for c in self.checks if c.status == ValidationStatus.WARN)
        return {
            "report_id": self.report_id,
            "title": self.title,
            "status": self.status.value,
            "checks": [c.to_dict() for c in self.checks],
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_ms": round(self.duration_ms, 2),
            "summary": {
                **self.summary,
                "total": len(self.checks),
                "passed": passed,
                "failed": failed,
                "warned": warned,
            },
        }

    def finalize(self) -> ValidationReport:
        self.completed_at = time.time()
        self.duration_ms = (self.completed_at - self.started_at) * 1000.0
        passed = sum(1 for c in self.checks if c.status == ValidationStatus.PASS)
        failed = sum(1 for c in self.checks if c.status == ValidationStatus.FAIL)
        warned = sum(1 for c in self.checks if c.status == ValidationStatus.WARN)
        self.summary.update({"total": len(self.checks), "passed": passed, "failed": failed, "warned": warned})
        if failed:
            self.status = ValidationStatus.FAIL
        elif warned:
            self.status = ValidationStatus.WARN
        else:
            self.status = ValidationStatus.PASS
        return self


@dataclass
class PlatformHealthReport:
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    overall_status: ValidationStatus = ValidationStatus.PASS
    readiness_level: ReadinessLevel = ReadinessLevel.PRODUCTION_READY
    components: dict[str, str] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    generated_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "overall_status": self.overall_status.value,
            "readiness_level": self.readiness_level.value,
            "components": dict(self.components),
            "metrics": dict(self.metrics),
            "generated_at": self.generated_at,
        }


@dataclass
class PerformanceBenchmark:
    name: str
    operations: int
    duration_ms: float
    throughput_ops_sec: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "operations": self.operations,
            "duration_ms": round(self.duration_ms, 2),
            "throughput_ops_sec": round(self.throughput_ops_sec, 2),
            "metadata": dict(self.metadata),
        }


@dataclass
class StressTestResult:
    scenario: str
    concurrency: int
    operations: int
    success_rate: float
    duration_ms: float
    recovered: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario": self.scenario,
            "concurrency": self.concurrency,
            "operations": self.operations,
            "success_rate": round(self.success_rate, 4),
            "duration_ms": round(self.duration_ms, 2),
            "recovered": self.recovered,
            "metadata": dict(self.metadata),
        }


@dataclass
class CertificationResult:
    certified: bool
    platform_version: str
    platform_status: str
    score: float
    gates_passed: int
    gates_total: int
    report: ValidationReport

    def to_dict(self) -> dict[str, Any]:
        return {
            "certified": self.certified,
            "platform_version": self.platform_version,
            "platform_status": self.platform_status,
            "score": self.score,
            "gates_passed": self.gates_passed,
            "gates_total": self.gates_total,
            "report": self.report.to_dict(),
        }
