"""Sprint 32.3 — canonical services, unified queue, secrets, metrics."""

from __future__ import annotations

import asyncio

from events.event_bus_policy import event_bus_policy
from platform_architecture.canonical_services import canonical_for, canonical_summary, list_canonical_services
from platform_architecture.consolidation_scanner import run_consolidation_scan
from platform_architecture.sprint_review import run_sprint_architecture_review
from platform_jobs.unified_queue import QueueLane, unified_queue
from platform_observability.enterprise_metrics import enterprise_metrics
from platform_security.secret_policy import scan_repo_for_insecure_defaults
from services.canonical_deal_pipeline import deal_pipeline_info, get_pipeline_engine


def test_canonical_registry_complete():
    services = {r["service"] for r in list_canonical_services()}
    assert {
        "deal_pipeline",
        "workflow_engine",
        "knowledge_base",
        "event_bus",
        "unified_queue",
        "notification_pipeline",
    } <= services
    assert canonical_summary()["principle"] == "one_responsibility_one_canonical_service"
    assert canonical_for("deal_pipeline")["path"].endswith("deal_pipeline_engine.py")


def test_deal_pipeline_canonical_entry():
    info = deal_pipeline_info()
    assert "deal_pipeline_engine" in info["canonical_model"]
    assert get_pipeline_engine().__name__ == "DealPipelineEngineV2"


def test_unified_queue_lanes_retry_dlq():
    async def _run() -> None:
        unified_queue.reset()
        assert set(unified_queue.lanes()) == {
            "ai",
            "workflow",
            "background",
            "notification",
            "render",
        }
        job = await unified_queue.enqueue(
            lane=QueueLane.AI,
            handler_name="test.ai",
            payload={"x": 1},
        )
        assert job.payload["_queue_lane"] == "ai"
        assert job.max_retries == 3
        # Exhaust retries → DLQ
        job.max_retries = 0
        job.retry_count = 0
        result = await unified_queue.fail_with_retry(job, "boom")
        assert result is None
        dlq = await unified_queue.dead_letter()
        assert any(j.job_id == job.job_id for j in dlq)
        snap = await unified_queue.snapshot()
        assert snap.dead_letter_total >= 1
        assert unified_queue.capabilities()["dead_letter"] is True

    asyncio.run(_run())


def test_secret_repo_scan_passes_after_n8n_hardening():
    report = scan_repo_for_insecure_defaults()
    assert report.passed, [f for f in report.findings if f.severity == "critical"]


def test_event_bus_policy_mandatory():
    policy = event_bus_policy()
    assert policy["mandatory_cross_module"] is True
    assert "PlatformEventBus" in policy["canonical"]


def test_enterprise_metrics_catalog():
    caps = enterprise_metrics.capabilities()
    names = set(caps["metrics"])
    assert "queue.wait_ms" in names
    assert "ai.cost_usd" in names
    assert "workflow.duration_ms" in names
    assert "cache.hit_rate" in names
    enterprise_metrics.record_api_latency(12.5, route="/health")
    enterprise_metrics.record_ai_cost(0.02, provider="openrouter")


def test_consolidation_and_sprint_review():
    cons = run_consolidation_scan()
    assert cons.passed, [f for f in cons.findings if f.severity == "critical"]
    review = run_sprint_architecture_review()
    assert review.passed, [f for f in review.findings if f.severity == "critical"]
