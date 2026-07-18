"""Tests — Platform Job & Automation Engine."""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from events.event_bus import reset_subscribers, subscribe
from platform_jobs.job_engine import job_engine
from platform_jobs.job_events import JobCompletedEvent, JobCreatedEvent, JobRetriedEvent
from platform_jobs.job_executor import job_executor
from platform_jobs.job_queue import job_queue
from platform_jobs.job_registry import job_registry
from platform_jobs.job_retry import job_retry
from platform_jobs.jobs_router import register_jobs_routes
from platform_jobs.models import JobRecord, JobState, JobType
from platform_jobs.worker_manager import worker_manager
from platform_management.management_router import register_management_routes
from platform_management.permissions import ManagementRole


@pytest.fixture(autouse=True)
def _reset_jobs():
    job_engine.reset()
    yield
    job_engine.reset()


@pytest.fixture
def actor_header():
    return {"X-Actor-Telegram-Id": "42"}


@pytest.fixture(autouse=True)
def _grant_owner(monkeypatch):
    async def _owner(_tid):
        return ManagementRole.OWNER

    monkeypatch.setattr("platform_management.permissions.resolve_role", _owner)


@pytest.fixture
def noop_handler():
    async def _handler(payload):
        return {"ok": True, **payload}

    job_registry.register("noop", _handler)
    return _handler


@pytest.fixture
def failing_handler():
    calls = {"count": 0}

    async def _handler(_payload):
        calls["count"] += 1
        raise RuntimeError("simulated failure")

    job_registry.register("failing", _handler)
    return calls


# ---- Scheduling ----

@pytest.mark.asyncio
async def test_enqueue_immediate(noop_handler):
    job = await job_engine.enqueue("noop", {"x": 1})
    assert job.job_type == JobType.IMMEDIATE.value
    assert job.state == JobState.PENDING.value
    assert await job_queue.size() == 1


@pytest.mark.asyncio
async def test_enqueue_delayed(noop_handler):
    job = await job_engine.enqueue(
        "noop",
        {},
        job_type=JobType.DELAYED,
        delay_seconds=60,
    )
    assert job.job_type == JobType.DELAYED.value
    assert job.run_at is not None


@pytest.mark.asyncio
async def test_enqueue_cron(noop_handler):
    job = await job_engine.enqueue(
        "noop",
        {},
        job_type=JobType.CRON,
        cron_expression="*/5 * * * *",
    )
    assert job.cron_expression == "*/5 * * * *"
    assert job.run_at is not None


@pytest.mark.asyncio
async def test_enqueue_scheduled(noop_handler):
    run_at = datetime.now(timezone.utc) + timedelta(hours=1)
    job = await job_engine.enqueue(
        "noop",
        {},
        job_type=JobType.SCHEDULED,
        run_at=run_at,
    )
    assert job.job_type == JobType.SCHEDULED.value


@pytest.mark.asyncio
async def test_job_created_event(noop_handler):
    reset_subscribers()
    received = []

    async def _capture(event):
        received.append(event)

    subscribe(JobCreatedEvent, _capture, handler_id="test_job_created")
    await job_engine.enqueue("noop", {})
    await asyncio.sleep(0.05)
    assert len(received) >= 1


# ---- Execution ----

@pytest.mark.asyncio
async def test_execute_job(noop_handler):
    job = await job_engine.enqueue("noop", {"value": 42})
    job.run_at = time.monotonic()
    result = await job_executor.execute(job, worker_id="w1")
    assert result["ok"] is True
    assert job.state == JobState.COMPLETED.value


@pytest.mark.asyncio
async def test_pipeline_execution(noop_handler):
    job_registry.register("step_a", lambda p: {"a": 1})
    job_registry.register("step_b", lambda p: {"b": p.get("a", 0) + 1})

    job = await job_engine.enqueue(
        "step_a",
        {},
        job_type=JobType.PIPELINE,
        pipeline_steps=["step_a", "step_b"],
    )
    job.run_at = time.monotonic()
    result = await job_executor.execute(job)
    assert result["step_b"]["b"] == 2


# ---- Retry ----

@pytest.mark.asyncio
async def test_retry_exponential_backoff(failing_handler):
    job = JobRecord.new("failing", {}, max_retries=3)
    job.run_at = time.monotonic()

    with pytest.raises(RuntimeError):
        await job_executor.execute(job)

    assert job.retry_count == 1
    assert job.state == JobState.RETRYING.value
    history = job_retry.history()
    assert history[-1]["delay_seconds"] == 1.0


@pytest.mark.asyncio
async def test_dead_letter_after_max_retries(failing_handler):
    job = JobRecord.new("failing", {}, max_retries=2)
    job.run_at = time.monotonic()

    for _ in range(3):
        try:
            await job_executor.execute(job)
        except RuntimeError:
            job.run_at = time.monotonic()

    dlq = await job_queue.dead_letter_queue()
    assert len(dlq) >= 1


# ---- Workers ----

@pytest.mark.asyncio
async def test_worker_pool(noop_handler):
    await worker_manager.start(count=4)
    assert len(worker_manager.list_workers()) == 4
    assert worker_manager.has_capacity()

    worker = worker_manager.acquire_worker()
    assert worker is not None
    assert worker.status == "busy"
    worker_manager.release_worker(worker.worker_id)
    assert worker.status == "idle"


@pytest.mark.asyncio
async def test_graceful_shutdown(noop_handler):
    await worker_manager.start(count=2)
    await worker_manager.shutdown(graceful=True)
    assert len(worker_manager.list_workers()) == 0


# ---- Queue ----

@pytest.mark.asyncio
async def test_priority_queue_order(noop_handler):
    jobs = [
        JobRecord.new("noop", {"n": 3}, priority=9),
        JobRecord.new("noop", {"n": 1}, priority=1),
        JobRecord.new("noop", {"n": 2}, priority=5),
    ]
    for j in jobs:
        j.run_at = time.monotonic()
    await job_queue.enqueue_many(jobs)

    first = await job_queue.dequeue_ready()
    assert first.priority == 1


@pytest.mark.asyncio
async def test_cancel_job(noop_handler):
    job = await job_engine.enqueue("noop", {})
    cancelled = await job_engine.cancel(job.job_id, reason="test")
    assert cancelled.state == JobState.CANCELLED.value


# ---- Events ----

@pytest.mark.asyncio
async def test_job_completed_event(noop_handler):
    reset_subscribers()
    events = []

    async def _capture(event):
        events.append(event)

    subscribe(JobCompletedEvent, _capture, handler_id="test_completed")

    job = JobRecord.new("noop", {})
    job.run_at = time.monotonic()
    await job_executor.execute(job)

    await asyncio.sleep(0.05)
    assert any(isinstance(e, JobCompletedEvent) for e in events)


# ---- Management API ----

@pytest.mark.asyncio
async def test_management_jobs_endpoint(actor_header, noop_handler):
    app = web.Application()
    register_management_routes(app)

    with patch("config.OWNER_ID", 42), patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(app)) as client:
            resp = await client.get("/management/jobs", headers=actor_header)
            assert resp.status == 200
            body = await resp.json()
            assert body["success"] is True
            assert "metrics" in body["data"]


@pytest.mark.asyncio
async def test_enqueue_via_api(actor_header, noop_handler):
    app = web.Application()
    register_jobs_routes(app)

    with patch("config.OWNER_ID", 42), patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(app)) as client:
            resp = await client.post(
                "/management/jobs",
                headers=actor_header,
                json={"handler_name": "noop", "payload": {"test": True}},
            )
            assert resp.status == 201


@pytest.mark.asyncio
async def test_dashboard_widgets(noop_handler):
    await job_engine.enqueue("noop", {})
    widgets = await job_engine.dashboard_widgets()
    assert "running_jobs" in widgets
    assert "queue_size" in widgets
    assert "worker_health" in widgets
    assert "execution_rate" in widgets


# ---- Performance ----

@pytest.mark.asyncio
async def test_performance_100k_enqueue(noop_handler):
    """Queue should handle 100k job enqueue efficiently."""
    jobs = [JobRecord.new("noop", {"i": i}, priority=5) for i in range(100_000)]
    for j in jobs:
        j.run_at = time.monotonic() + 3600

    started = time.perf_counter()
    await job_queue.enqueue_many(jobs)
    elapsed = time.perf_counter() - started

    size = await job_queue.size()
    assert size == 100_000
    assert elapsed < 30.0
