# Sprint 8.8 — Production validation and commercial release models.

from __future__ import annotations

import enum
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


def _id() -> str:
    return str(uuid.uuid4())


def _ts() -> float:
    return time.time()


class CheckStatus(str, enum.Enum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


class ReportKind(str, enum.Enum):
    PRODUCTION = "production"
    QUALITY = "quality"
    SECURITY = "security"
    PERFORMANCE = "performance"
    COMPATIBILITY = "compatibility"
    DEPLOYMENT = "deployment"


@dataclass
class ValidationCheck:
    check_id: str = field(default_factory=_id)
    name: str = ""
    category: str = ""
    status: CheckStatus = CheckStatus.PASSED
    detail: str = ""
    duration_ms: float = 0.0
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "name": self.name,
            "category": self.category,
            "status": self.status.value,
            "detail": self.detail,
            "duration_ms": self.duration_ms,
            "created_at": self.created_at,
        }


@dataclass
class ValidationReport:
    report_id: str = field(default_factory=_id)
    kind: ReportKind = ReportKind.PRODUCTION
    title: str = ""
    summary: str = ""
    passed: int = 0
    failed: int = 0
    warnings: int = 0
    checks: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    @property
    def ok(self) -> bool:
        return self.failed == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "kind": self.kind.value,
            "title": self.title,
            "summary": self.summary,
            "passed": self.passed,
            "failed": self.failed,
            "warnings": self.warnings,
            "ok": self.ok,
            "checks": list(self.checks),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }


@dataclass
class ReleaseRecord:
    release_id: str = field(default_factory=_id)
    version: str = "2.0.0"
    status: str = "Production Ready"
    release_type: str = "Commercial"
    notes: str = ""
    certified: bool = False
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "release_id": self.release_id,
            "version": self.version,
            "status": self.status,
            "release_type": self.release_type,
            "notes": self.notes,
            "certified": self.certified,
            "created_at": self.created_at,
        }


@dataclass
class ReadinessSnapshot:
    snapshot_id: str = field(default_factory=_id)
    ready: bool = False
    score: float = 0.0
    checks: list[dict[str, Any]] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "ready": self.ready,
            "score": self.score,
            "checks": list(self.checks),
            "blockers": list(self.blockers),
            "created_at": self.created_at,
        }
