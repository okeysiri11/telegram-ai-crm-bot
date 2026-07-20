# TraceManager — distributed tracing with cross-service correlation.

from __future__ import annotations

from typing import Any

from platform_observability.models import MonitoringContext, SpanKind
from platform_observability.tracing_service import TracingService, tracing_service


class TraceManager:
    def __init__(self, *, tracing: TracingService | None = None) -> None:
        self._tracing = tracing or tracing_service
        self._export_buffer: list[dict[str, Any]] = []

    def reset(self) -> None:
        self._tracing.reset()
        self._export_buffer.clear()

    def start_request_trace(self, name: str, ctx: MonitoringContext) -> str:
        span = self._tracing.start_trace(name, component=ctx.component or "platform")
        if ctx.agent_id:
            span.attributes["agent_id"] = ctx.agent_id
        if ctx.workflow_id:
            span.attributes["workflow_id"] = ctx.workflow_id
        ctx.trace_id = span.trace_id
        ctx.correlation_id = ctx.correlation_id or span.trace_id
        return span.trace_id

    def trace_workflow(self, workflow_id: str, name: str, *, trace_id: str | None = None):
        span = self._tracing.start_span(
            name,
            component="workflow",
            trace_id=trace_id,
            kind=SpanKind.SERVER.value,
        )
        span.attributes["workflow_id"] = workflow_id
        return span

    def trace_task(self, task_id: str, name: str, *, trace_id: str | None = None):
        span = self._tracing.start_span(name, component="task", trace_id=trace_id)
        span.attributes["task_id"] = task_id
        return span

    def trace_agent(self, agent_id: str, name: str, *, trace_id: str | None = None):
        span = self._tracing.start_span(name, component="agent", trace_id=trace_id)
        span.attributes["agent_id"] = agent_id
        return span

    def trace_tool(self, tool_id: str, name: str, *, trace_id: str | None = None):
        span = self._tracing.start_span(name, component="tool", trace_id=trace_id, kind=SpanKind.CLIENT.value)
        span.attributes["tool_id"] = tool_id
        return span

    def end_span(self, span, *, status: str = "ok") -> None:
        self._tracing.end_span(span, status=status)
        self._export_buffer.append(span.to_dict())

    def get_trace(self, trace_id: str) -> list[dict[str, Any]]:
        return self._tracing.get_trace(trace_id)

    def export_traces(self, *, limit: int = 100) -> list[dict[str, Any]]:
        batch = self._export_buffer[:limit]
        self._export_buffer = self._export_buffer[limit:]
        if not batch:
            return self._tracing.query(limit=limit)
        return batch

    def slowest(self, *, limit: int = 10) -> list[dict[str, Any]]:
        return self._tracing.slowest(limit=limit)


trace_manager = TraceManager()
