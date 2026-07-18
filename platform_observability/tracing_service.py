# Distributed tracing service.

from __future__ import annotations

import uuid
from contextvars import ContextVar
from typing import Any

from platform_observability.models import SpanKind, TraceSpan

_current_trace: ContextVar[str | None] = ContextVar("trace_id", default=None)
_current_span: ContextVar[str | None] = ContextVar("span_id", default=None)


class TracingService:
    COMPONENTS = (
        "management_api",
        "sdk",
        "workflow",
        "event_bus",
        "jobs",
        "integrations",
        "realtime",
    )

    def __init__(self, *, max_spans: int = 20_000) -> None:
        self._spans: list[TraceSpan] = []
        self._traces: dict[str, list[str]] = {}
        self._max_spans = max_spans

    def reset(self) -> None:
        self._spans.clear()
        self._traces.clear()

    def start_trace(self, name: str, *, component: str) -> TraceSpan:
        trace_id = str(uuid.uuid4())
        span = TraceSpan.new(trace_id=trace_id, name=name, component=component, kind=SpanKind.SERVER.value)
        _current_trace.set(trace_id)
        _current_span.set(span.span_id)
        self._store(span)
        return span

    def start_span(
        self,
        name: str,
        *,
        component: str,
        kind: str = SpanKind.INTERNAL.value,
        trace_id: str | None = None,
    ) -> TraceSpan:
        tid = trace_id or _current_trace.get() or str(uuid.uuid4())
        parent = _current_span.get()
        span = TraceSpan.new(
            trace_id=tid,
            name=name,
            component=component,
            parent_span_id=parent,
            kind=kind,
        )
        _current_trace.set(tid)
        _current_span.set(span.span_id)
        self._store(span)
        return span

    def end_span(self, span: TraceSpan, *, status: str = "ok") -> None:
        span.finish(status=status)

    def _store(self, span: TraceSpan) -> None:
        self._spans.append(span)
        self._traces.setdefault(span.trace_id, []).append(span.span_id)
        if len(self._spans) > self._max_spans:
            self._spans = self._spans[-self._max_spans :]

    def get_trace(self, trace_id: str) -> list[dict[str, Any]]:
        span_ids = set(self._traces.get(trace_id, []))
        return [s.to_dict() for s in self._spans if s.span_id in span_ids]

    def query(
        self,
        *,
        component: str | None = None,
        trace_id: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        spans = self._spans
        if component:
            spans = [s for s in spans if s.component == component]
        if trace_id:
            spans = [s for s in spans if s.trace_id == trace_id]
        return [s.to_dict() for s in spans[-limit:]]

    def slowest(self, *, limit: int = 10) -> list[dict[str, Any]]:
        finished = [s for s in self._spans if s.ended_at is not None]
        finished.sort(key=lambda s: s.duration_ms, reverse=True)
        return [s.to_dict() for s in finished[:limit]]


tracing_service = TracingService()
