"""Tests — Platform Observability."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from events.event_bus import reset_subscribers, subscribe
from platform_management.management_router import register_management_routes
from platform_management.permissions import ManagementRole
from platform_observability.alert_manager import alert_manager
from platform_observability.anomaly_detector import anomaly_detector
from platform_observability.logging_service import logging_service
from platform_observability.metrics_service import metrics_service
from platform_observability.models import AlertSeverity
from platform_observability.observability_events import AlertRaisedEvent, AlertResolvedEvent
from platform_observability.performance_monitor import performance_monitor
from platform_observability.retention_manager import retention_manager
from platform_observability.telemetry_router import register_observability_routes
from platform_observability.tracing_service import tracing_service


@pytest.fixture(autouse=True)
def _reset_obs():
    metrics_service.reset()
    logging_service.reset()
    tracing_service.reset()
    alert_manager.reset()
    performance_monitor.reset()
    anomaly_detector.reset()
    retention_manager.reset()
    yield


@pytest.fixture(autouse=True)
def _grant_owner(monkeypatch):
    async def _owner(_tid):
        return ManagementRole.OWNER

    monkeypatch.setattr("platform_management.permissions.resolve_role", _owner)


# ---- Metrics ----

def test_record_metric():
    metrics_service.record("test.metric", 42.0, unit="count")
    summary = metrics_service.summary()
    assert "test.metric" in summary
    assert summary["test.metric"]["last"] == 42.0


def test_metric_catalog():
    catalog = metrics_service.catalog()
    assert "system.cpu.percent" in catalog
    assert "jobs.queue.size" in catalog
    assert "realtime.connections.count" in catalog


@pytest.mark.asyncio
async def test_collect_platform_metrics():
    with patch.object(metrics_service, "_collect_postgresql", return_value=[]), patch.object(
        metrics_service, "_collect_redis", return_value=[]
    ):
        points = await metrics_service.collect_platform_metrics()
    assert len(points) >= 2


@pytest.mark.asyncio
async def test_batch_metric_export():
    for i in range(150):
        metrics_service.record(f"batch.{i}", float(i))
    batch = await metrics_service.flush_export_buffer()
    assert len(batch) == 100


# ---- Logging ----

def test_structured_logging():
    logging_service.set_context(
        correlation_id="corr-1",
        request_id="req-1",
        user_id=42,
        job_id="job-1",
        workflow_id="wf-1",
    )
    entry = logging_service.info("test message", component="test")
    assert entry.correlation_id == "corr-1"
    assert entry.user_id == 42
    assert entry.job_id == "job-1"

    logs = logging_service.query(correlation_id="corr-1")
    assert len(logs) == 1
    assert logs[0]["level"] == "INFO"


# ---- Tracing ----

def test_distributed_trace():
    trace = tracing_service.start_trace("GET /management/system", component="management_api")
    child = tracing_service.start_span("resolve_role", component="management_api")
    tracing_service.end_span(child)
    tracing_service.end_span(trace)

    spans = tracing_service.get_trace(trace.trace_id)
    assert len(spans) == 2
    assert spans[0]["component"] == "management_api"


def test_slowest_traces():
    from datetime import datetime, timedelta, timezone

    t1 = tracing_service.start_trace("slow", component="management_api")
    t1.started_at = datetime.now(timezone.utc) - timedelta(milliseconds=500)
    t1.finish()
    t2 = tracing_service.start_trace("fast", component="sdk")
    t2.started_at = datetime.now(timezone.utc) - timedelta(milliseconds=10)
    t2.finish()
    slowest = tracing_service.slowest(limit=1)
    assert slowest[0]["duration_ms"] >= 400


# ---- Alerts ----

@pytest.mark.asyncio
async def test_alert_lifecycle():
    with patch("events.event_bus.publish", new_callable=AsyncMock):
        alert = await alert_manager.raise_alert(
            name="high_cpu",
            severity=AlertSeverity.WARNING.value,
            source="metrics",
            message="CPU > 80%",
        )
        assert alert is not None
        assert alert.state == "open"

        resolved = await alert_manager.resolve(alert.alert_id)
        assert resolved.state == "recovered"


@pytest.mark.asyncio
async def test_alert_deduplication():
    with patch("events.event_bus.publish", new_callable=AsyncMock):
        a1 = await alert_manager.raise_alert(
            name="dup",
            severity=AlertSeverity.WARNING.value,
            source="test",
            message="first",
        )
        a2 = await alert_manager.raise_alert(
            name="dup",
            severity=AlertSeverity.WARNING.value,
            source="test",
            message="second",
        )
        assert a1.alert_id == a2.alert_id
        assert a2.count == 2


@pytest.mark.asyncio
async def test_alert_events():
    reset_subscribers()
    events = []

    async def _capture(event):
        events.append(event)

    subscribe(AlertRaisedEvent, _capture, handler_id="test_alert")
    with patch("platform_observability.logging_service.logging_service.warning"):
        await alert_manager.raise_alert(
            name="evt",
            severity=AlertSeverity.CRITICAL.value,
            source="test",
            message="critical",
        )
    await asyncio.sleep(0.05)
    assert any(isinstance(e, AlertRaisedEvent) for e in events)


# ---- Performance ----

def test_slow_request_detection():
    performance_monitor.record_request(path="/api/slow", method="GET", duration_ms=1500)
    performance_monitor.record_request(path="/api/fast", method="GET", duration_ms=50)
    slow = performance_monitor.slowest_apis()
    assert slow[0]["endpoint"] == "GET /api/slow"
    assert len(performance_monitor.slow_requests()) == 1


# ---- Retention ----

def test_retention_policy():
    retention_manager.set_policy(metrics_days=7, logs_days=3)
    policy = retention_manager.get_policy()
    assert policy.metrics_days == 7
    assert policy.logs_days == 3

    metrics_service.record("old", 1)
    purged = retention_manager.apply()
    assert "metrics" in purged


# ---- Anomaly ----

@pytest.mark.asyncio
async def test_anomaly_detection():
    metrics_service.record("jobs.queue.size", 5000)
    summary = metrics_service.summary()
    with patch("events.event_bus.publish", new_callable=AsyncMock), patch(
        "platform_observability.logging_service.logging_service.warning"
    ):
        anomalies = await anomaly_detector.analyze(summary)
    assert any(a["metric"] == "jobs.queue.size" for a in anomalies)


# ---- Management API ----

@pytest.mark.asyncio
async def test_management_observability_endpoint(actor_header):
    app = web.Application()
    register_management_routes(app)

    with patch("config.OWNER_ID", 42), patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ), patch.object(metrics_service, "_collect_postgresql", return_value=[]), patch.object(
        metrics_service, "_collect_redis", return_value=[]
    ):
        async with TestClient(TestServer(app)) as client:
            resp = await client.get("/management/observability", headers=actor_header)
            assert resp.status == 200
            body = await resp.json()
            assert body["success"] is True
            assert "health" in body["data"]
            assert "metrics_summary" in body["data"]


@pytest.mark.asyncio
async def test_metrics_endpoint(actor_header):
    app = web.Application()
    register_observability_routes(app)

    with patch("config.OWNER_ID", 42), patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ), patch.object(metrics_service, "collect_platform_metrics", new_callable=AsyncMock):
        async with TestClient(TestServer(app)) as client:
            resp = await client.get("/management/observability/metrics", headers=actor_header)
            assert resp.status == 200


@pytest.mark.asyncio
async def test_permissions_denied(actor_header, monkeypatch):
    app = web.Application()
    register_observability_routes(app)

    async def _readonly(_tid):
        return ManagementRole.READ_ONLY

    monkeypatch.setattr("platform_management.permissions.resolve_role", _readonly)

    with patch(
        "platform_identity.identity_service.identity_service.authenticate_telegram",
        new_callable=AsyncMock,
    ), patch(
        "platform_identity.identity_service.identity_service.authorize",
        new_callable=AsyncMock,
        return_value=False,
    ), patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(app)) as client:
            resp = await client.get("/management/observability", headers=actor_header)
            assert resp.status == 403


# ---- Performance ----

def test_low_overhead_logging():
    import time

    started = time.perf_counter()
    for i in range(1000):
        logging_service.info(f"log {i}", component="perf")
    elapsed = time.perf_counter() - started
    assert elapsed < 2.0
    assert len(logging_service._entries) == 1000
