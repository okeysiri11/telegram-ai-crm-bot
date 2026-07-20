"""Tests — Platform Observability Layer (Sprint 5.2)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from platform_observability.alert_manager import AlertManager
from platform_observability.config import DEFAULT_ALERT_THRESHOLDS
from platform_observability.diagnostic_manager import DiagnosticManager
from platform_observability.health_manager import HealthManager
from platform_observability.log_manager import LogManager
from platform_observability.logging_service import LoggingService
from platform_observability.metrics_manager import MetricsManager
from platform_observability.metrics_service import MetricsService
from platform_observability.models import AlertThreshold, MonitoringContext
from platform_observability.observability_manager import ObservabilityManager
from platform_observability.telemetry_collector import TelemetryCollector
from platform_observability.trace_manager import TraceManager
from platform_observability.tracing_service import TracingService


@pytest.fixture
def obs() -> ObservabilityManager:
    logs = LogManager(logging=LoggingService())
    traces = TraceManager(tracing=TracingService())
    metrics = MetricsManager(metrics=MetricsService())
    mgr = ObservabilityManager(
        logs=logs,
        traces=traces,
        metrics=metrics,
        health=HealthManager(),
        alerts=AlertManager(),
        diagnostics=DiagnosticManager(logs=logs, traces=traces, metrics=metrics),
        telemetry=TelemetryCollector(metrics=metrics, alerts=AlertManager()),
    )
    yield mgr
    mgr.reset()


def test_structured_logging_with_context(obs: ObservabilityManager):
    ctx = MonitoringContext(
        correlation_id="corr-1",
        request_id="req-1",
        workflow_id="wf-1",
        agent_id="auto_agent",
        task_id="task-1",
    )
    obs.bind_context(ctx)
    obs._logs.info("Test message", component="workflow")
    logs = obs.query_logs(workflow_id="wf-1", agent_id="auto_agent")
    assert len(logs) >= 1
    assert logs[-1]["correlation_id"] == "corr-1"
    assert logs[-1]["agent_id"] == "auto_agent"


def test_log_filtering_by_level(obs: ObservabilityManager):
    obs._logs.error("Error occurred", component="test")
    obs._logs.info("Info message", component="test")
    errors = obs.query_logs(level="ERROR")
    assert all(l["level"] == "ERROR" for l in errors)


def test_distributed_tracing_workflow(obs: ObservabilityManager):
    ctx = MonitoringContext(workflow_id="wf-trace", component="workflow")
    trace_id = obs._traces.start_request_trace("execute_workflow", ctx)
    span = obs._traces.trace_task("task-1", "run_step", trace_id=trace_id)
    obs._traces.end_span(span)
    exported = obs.export_traces()
    assert len(exported) >= 1


def test_agent_and_tool_tracing(obs: ObservabilityManager):
    agent_span = obs._traces.trace_agent("auto_agent", "reason")
    tool_span = obs._traces.trace_tool("crm_lookup", "execute")
    obs._traces.end_span(agent_span)
    obs._traces.end_span(tool_span)
    slowest = obs._traces.slowest(limit=5)
    assert len(slowest) >= 1


def test_metrics_record_and_summary(obs: ObservabilityManager):
    obs._metrics.record("workflow.duration_ms", 1200.0, unit="ms")
    obs._metrics.record("tool.latency_ms", 50.0, unit="ms")
    obs._metrics.record("agent.latency_ms", 300.0, unit="ms")
    summary = obs.metrics_summary()
    assert "workflow.duration_ms" in summary


@pytest.mark.asyncio
async def test_health_monitoring(obs: ObservabilityManager):
    health = await obs.check_health()
    assert "overall_status" in health
    assert "platform_engines" in health
    assert "workflow" in health["platform_engines"]


@pytest.mark.asyncio
async def test_alert_threshold_evaluation(obs: ObservabilityManager):
    obs._metrics.record("system.memory.percent", 95.0, unit="percent")
    obs.configure_alert(AlertThreshold("test_mem", "system.memory.percent", "gt", 90.0, "critical"))
    raised = await obs._telemetry.evaluate_alerts()
    assert isinstance(raised, list)


@pytest.mark.asyncio
async def test_raise_alert(obs: ObservabilityManager):
    with patch("platform_observability.logging_service.logging_service.warning"):
        alert = await obs.raise_alert(name="test_alert", severity="warning", source="test", message="test")
    assert alert is not None
    assert alert.name == "test_alert"


@pytest.mark.asyncio
async def test_diagnostics_report(obs: ObservabilityManager):
    obs._logs.error("Simulated failure", component="workflow")
    report = await obs.diagnose(title="Test Report")
    assert report.title == "Test Report"
    assert "metrics" in report.performance
    assert isinstance(report.failures, list)


@pytest.mark.asyncio
async def test_telemetry_collection_cycle(obs: ObservabilityManager):
    with patch.object(obs._metrics, "collect_all", return_value=[]), patch.object(
        obs._metrics, "collect_platform_engines", return_value={}
    ):
        result = await obs.collect_telemetry()
    assert "metrics_collected" in result


def test_monitoring_context_to_dict():
    ctx = MonitoringContext(correlation_id="c1", agent_id="a1")
    d = ctx.to_dict()
    assert d["correlation_id"] == "c1"
    assert d["agent_id"] == "a1"


def test_default_alert_thresholds():
    assert len(DEFAULT_ALERT_THRESHOLDS) >= 6
    mem = next(t for t in DEFAULT_ALERT_THRESHOLDS if t.name == "memory_pressure")
    assert mem.evaluate(95.0) is True
    assert mem.evaluate(50.0) is False


def test_integrations_context():
    from platform_observability.integrations import observability_integrations

    ctx = observability_integrations.context_from_request(request_id="r1", agent_id="auto_agent")
    assert ctx.correlation_id
    assert ctx.agent_id == "auto_agent"


@pytest.mark.asyncio
async def test_log_retention_interface(obs: ObservabilityManager):
    obs._logs.set_retention(logs_days=14)
    purged = obs._logs.purge_expired()
    assert isinstance(purged, dict)


@pytest.mark.asyncio
async def test_trace_export_interface(obs: ObservabilityManager):
    span = obs._traces.trace_workflow("wf-1", "test")
    obs._traces.end_span(span)
    batch = obs._traces.export_traces(limit=10)
    assert isinstance(batch, list)


def test_observability_manager_create_context(obs: ObservabilityManager):
    ctx = obs.create_context(workflow_id="wf-99", agent_id="agent-x")
    assert ctx.workflow_id == "wf-99"
