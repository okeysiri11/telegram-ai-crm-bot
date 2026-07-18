# Observability domain models.

from __future__ import annotations

import enum
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


class AlertSeverity(str, enum.Enum):
    WARNING = "warning"
    CRITICAL = "critical"


class AlertState(str, enum.Enum):
    OPEN = "open"
    RECOVERED = "recovered"
    SUPPRESSED = "suppressed"


class SpanKind(str, enum.Enum):
    SERVER = "server"
    CLIENT = "client"
    INTERNAL = "internal"
    PRODUCER = "producer"
    CONSUMER = "consumer"


@dataclass
class MetricPoint:
    name: str
    value: float
    unit: str = "count"
    tags: dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "tags": self.tags,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class StructuredLogEntry:
    level: str
    message: str
    correlation_id: str
    request_id: str | None = None
    user_id: int | None = None
    job_id: str | None = None
    workflow_id: str | None = None
    component: str = "platform"
    extra: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level,
            "message": self.message,
            "correlation_id": self.correlation_id,
            "request_id": self.request_id,
            "user_id": self.user_id,
            "job_id": self.job_id,
            "workflow_id": self.workflow_id,
            "component": self.component,
            "extra": self.extra,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class TraceSpan:
    trace_id: str
    span_id: str
    name: str
    component: str
    kind: str = SpanKind.INTERNAL.value
    parent_span_id: str | None = None
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: datetime | None = None
    duration_ms: float = 0.0
    status: str = "ok"
    attributes: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def new(
        *,
        trace_id: str,
        name: str,
        component: str,
        parent_span_id: str | None = None,
        kind: str = SpanKind.INTERNAL.value,
    ) -> TraceSpan:
        return TraceSpan(
            trace_id=trace_id,
            span_id=str(uuid.uuid4()),
            name=name,
            component=component,
            parent_span_id=parent_span_id,
            kind=kind,
        )

    def finish(self, *, status: str = "ok") -> None:
        self.ended_at = datetime.now(timezone.utc)
        self.duration_ms = round((self.ended_at - self.started_at).total_seconds() * 1000, 2)
        self.status = status

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "name": self.name,
            "component": self.component,
            "kind": self.kind,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "attributes": self.attributes,
        }


@dataclass
class AlertRecord:
    alert_id: str
    name: str
    severity: str
    state: str
    source: str
    message: str
    fingerprint: str
    raised_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: datetime | None = None
    count: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "name": self.name,
            "severity": self.severity,
            "state": self.state,
            "source": self.source,
            "message": self.message,
            "fingerprint": self.fingerprint,
            "raised_at": self.raised_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "count": self.count,
        }


@dataclass
class RetentionPolicy:
    metrics_days: int = 30
    logs_days: int = 14
    traces_days: int = 7
    alerts_days: int = 90

    def to_dict(self) -> dict[str, int]:
        return {
            "metrics_days": self.metrics_days,
            "logs_days": self.logs_days,
            "traces_days": self.traces_days,
            "alerts_days": self.alerts_days,
        }
