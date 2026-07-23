"""Distributed tracing — request timeline across services."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class DistributedTracing:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def start(self, *, name: str, correlation_id: str = "") -> dict[str, Any]:
        if not name:
            raise ValidationError("name required")
        tid = _id("obs_trace")
        return self.store.obs_traces.save(
            tid,
            {
                "trace_id": tid,
                "name": name,
                "correlation_id": correlation_id or _id("corr"),
                "spans": [],
                "status": "open",
                "at": _now(),
            },
        )

    def span(
        self,
        *,
        trace_id: str,
        service: str,
        operation: str,
        duration_ms: float = 0.0,
    ) -> dict[str, Any]:
        trace = self.store.obs_traces.get(trace_id)
        if trace is None:
            raise NotFoundError(f"trace not found: {trace_id}")
        span = {
            "span_id": _id("obs_span"),
            "service": service,
            "operation": operation,
            "duration_ms": float(duration_ms),
            "at": _now(),
        }
        spans = list(trace.get("spans") or [])
        spans.append(span)
        trace["spans"] = spans
        trace["at"] = _now()
        self.store.obs_traces.save(trace_id, trace)
        return span

    def finish(self, *, trace_id: str, status: str = "ok") -> dict[str, Any]:
        trace = self.store.obs_traces.get(trace_id)
        if trace is None:
            raise NotFoundError(f"trace not found: {trace_id}")
        trace["status"] = status
        trace["at"] = _now()
        return self.store.obs_traces.save(trace_id, trace)

    def status(self) -> dict[str, Any]:
        return {"traces": self.store.obs_traces.count()}
