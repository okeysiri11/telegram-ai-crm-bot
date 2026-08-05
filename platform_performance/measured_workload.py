"""Measured enterprise workload harness — Sprint 37.3.

Runs real in-process microbenchmarks (not synthetic stubs). Extends
``platform_performance``; does not replace the Sprint 21.7 certification façade.
"""

from __future__ import annotations

import asyncio
import gc
import math
import os
import statistics
import time
import tracemalloc
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

AsyncFn = Callable[[], Awaitable[Any]]
SyncFn = Callable[[], Any]


@dataclass
class BenchResult:
    name: str
    iterations: int
    samples_ms: list[float] = field(default_factory=list)
    errors: int = 0
    notes: str = ""

    @property
    def p50_ms(self) -> float:
        return _percentile(self.samples_ms, 0.50)

    @property
    def p95_ms(self) -> float:
        return _percentile(self.samples_ms, 0.95)

    @property
    def avg_ms(self) -> float:
        return float(statistics.fmean(self.samples_ms)) if self.samples_ms else 0.0

    @property
    def throughput_ops_s(self) -> float:
        total_s = sum(self.samples_ms) / 1000.0
        if total_s <= 0:
            return 0.0
        return len(self.samples_ms) / total_s

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "iterations": self.iterations,
            "errors": self.errors,
            "p50_ms": round(self.p50_ms, 3),
            "p95_ms": round(self.p95_ms, 3),
            "avg_ms": round(self.avg_ms, 3),
            "throughput_ops_s": round(self.throughput_ops_s, 1),
            "notes": self.notes,
        }


def _percentile(samples: list[float], q: float) -> float:
    if not samples:
        return 0.0
    ordered = sorted(samples)
    idx = min(len(ordered) - 1, max(0, int(math.ceil(q * len(ordered)) - 1)))
    return float(ordered[idx])


async def _time_async(fn: AsyncFn, iterations: int, *, warmup: int = 2) -> BenchResult:
    name = getattr(fn, "__name__", "async_fn")
    samples: list[float] = []
    errors = 0
    for i in range(warmup + iterations):
        started = time.perf_counter()
        try:
            await fn()
        except Exception:  # noqa: BLE001
            errors += 1
        elapsed = (time.perf_counter() - started) * 1000.0
        if i >= warmup:
            samples.append(elapsed)
    return BenchResult(name=name, iterations=iterations, samples_ms=samples, errors=errors)


def _time_sync(fn: SyncFn, iterations: int, *, warmup: int = 2) -> BenchResult:
    name = getattr(fn, "__name__", "sync_fn")
    samples: list[float] = []
    errors = 0
    for i in range(warmup + iterations):
        started = time.perf_counter()
        try:
            fn()
        except Exception:  # noqa: BLE001
            errors += 1
        elapsed = (time.perf_counter() - started) * 1000.0
        if i >= warmup:
            samples.append(elapsed)
    return BenchResult(name=name, iterations=iterations, samples_ms=samples, errors=errors)


async def _bench_event_loop_lag(samples: int = 40) -> BenchResult:
    """Detect event-loop blocking by measuring scheduling lag under sleep(0)."""
    lags: list[float] = []
    for _ in range(samples):
        expected = time.perf_counter()
        await asyncio.sleep(0)
        lags.append((time.perf_counter() - expected) * 1000.0)
    return BenchResult(
        name="event_loop_lag",
        iterations=samples,
        samples_ms=lags,
        notes="sleep(0) scheduling lag; p95>5ms suggests loop pressure",
    )


async def _bench_cache() -> BenchResult:
    from platform_state.cache import platform_cache
    from platform_state.telemetry import enterprise_telemetry

    enterprise_telemetry.reset()
    platform_cache.reset()

    def _work() -> None:
        for i in range(200):
            key = f"k{i % 50}"
            if platform_cache.queries.get(key) is None:
                platform_cache.queries.set(key, {"i": i})
            platform_cache.queries.get(key)

    result = _time_sync(_work, iterations=30, warmup=3)
    result.name = "platform_cache_lru"
    result.notes = f"hit_rate={enterprise_telemetry.cache_hit_rate():.3f}"
    return result


async def _bench_pagination() -> BenchResult:
    from platform_api.pagination import PaginationMeta, PaginationParams

    def _work() -> None:
        p = PaginationParams.from_query({"page": "3", "page_size": "25"})
        assert p.offset == 50
        meta = PaginationMeta.build(page=p.page, page_size=p.page_size, total=1000)
        assert meta.has_next is True

    result = _time_sync(_work, iterations=500, warmup=20)
    result.name = "pagination_contract"
    return result


async def _bench_permission_engine() -> BenchResult:
    from platform_security.permission_engine import PermissionContext, permission_resolver

    ctx = PermissionContext(principal_id="bench", roles=["owner"], permissions=["*"])

    def _work() -> None:
        permission_resolver.allow(ctx, "workflow.execute")
        permission_resolver.allow(ctx, "ai.runtime")

    result = _time_sync(_work, iterations=400, warmup=20)
    result.name = "permission_engine"
    permission_resolver.cache.clear()
    return result


async def _bench_ai_runtime_guard() -> BenchResult:
    from platform_security.ai_security_center import AiSecurityCenter

    center = AiSecurityCenter()

    def _work() -> None:
        center.guard_prompt("Summarize Q2 pipeline for tenant A", actor="bench")

    result = _time_sync(_work, iterations=100, warmup=5)
    result.name = "ai_prompt_firewall"
    return result


async def _bench_ai_runtime_execute() -> BenchResult:
    from platform_ai.models import AIResponse
    from platform_ai.runtime_engine import AIRuntimeEngine
    from platform_ai import runtime_engine as re_mod

    engine = AIRuntimeEngine()
    engine.reset()

    async def fake_complete(req):
        return AIResponse(
            request_id=req.request_id,
            provider_id="bench",
            model_id="bench",
            content="ok",
        )

    original_init = re_mod.ai_service.initialize
    original_complete = re_mod.ai_service.complete
    re_mod.ai_service.initialize = lambda: None  # type: ignore[method-assign]
    re_mod.ai_service.complete = fake_complete  # type: ignore[method-assign]

    async def _once() -> None:
        await engine.execute({"prompt": "Summarize CRM pipeline for my tenant"})

    try:
        result = await _time_async(_once, iterations=25, warmup=3)
    finally:
        re_mod.ai_service.initialize = original_init  # type: ignore[method-assign]
        re_mod.ai_service.complete = original_complete  # type: ignore[method-assign]
    result.name = "ai_runtime_execute"
    result.notes = "provider mocked; measures runtime+firewall overhead"
    return result


async def _bench_workflow_task_queue() -> BenchResult:
    from platform_workflow.models import Task, TaskPriority, TaskType
    from platform_workflow.task_queue import TaskQueue

    queue = TaskQueue()

    async def _once() -> None:
        queue.reset()
        for i in range(40):
            task = Task(
                task_id=f"t{i}",
                workflow_id="wf_bench",
                step_id=f"s{i}",
                task_type=TaskType.SYSTEM,
                priority=TaskPriority.NORMAL,
            )
            await queue.enqueue(task)
        while True:
            item = await queue.dequeue_ready()
            if item is None:
                break

    result = await _time_async(_once, iterations=25, warmup=3)
    result.name = "workflow_task_queue"
    return result


async def _bench_multi_agent_plan() -> BenchResult:
    from platform_orchestrator.multi_agent_engine import multi_agent_runtime_engine

    engine = multi_agent_runtime_engine
    if hasattr(engine, "reset"):
        engine.reset()

    def _once() -> None:
        engine.plan({"goal": "benchmark concurrent agents", "mode": "sequential"})

    result = _time_sync(_once, iterations=20, warmup=2)
    result.name = "multi_agent_plan"
    return result


async def _bench_event_bus_inprocess() -> BenchResult:
    from events.base_event import BaseEvent
    from events.event_bus import PlatformEventBus

    hits = {"n": 0}

    @dataclass(kw_only=True)
    class BenchPing(BaseEvent):
        payload: dict[str, Any] = field(default_factory=dict)

    async def handler(_event: BaseEvent) -> None:
        hits["n"] += 1

    PlatformEventBus.subscribe(BenchPing, handler, handler_id="bench_37_3")

    async def _once() -> None:
        await PlatformEventBus.publish(BenchPing(payload={"i": 1}), wait=True)

    result = await _time_async(_once, iterations=60, warmup=5)
    result.name = "event_bus_inprocess"
    result.notes = f"handler_hits={hits['n']}"
    return result


async def _bench_memory_search() -> BenchResult:
    from platform_memory.project_memory_engine import project_memory_engine

    engine = project_memory_engine
    if hasattr(engine, "reset"):
        engine.reset()

    async def _once() -> None:
        await engine.search("enterprise crm", limit=10)

    result = await _time_async(_once, iterations=12, warmup=2)
    result.name = "project_memory"
    return result


async def _bench_knowledge_search() -> BenchResult:
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "knowledge"

    def _work() -> None:
        matches = list(root.rglob("*.md"))[:80]
        _ = sum(len(p.name) for p in matches)

    result = _time_sync(_work, iterations=15, warmup=2)
    result.name = "knowledge_search"
    result.notes = "filesystem knowledge index scan"
    return result


async def _bench_creative_factory() -> BenchResult:
    from platform_ai.creative_engine import creative_factory_engine

    engine = creative_factory_engine
    if hasattr(engine, "reset"):
        engine.reset()

    def _once() -> None:
        engine.list_assets()
        engine.list_campaigns()

    result = _time_sync(_once, iterations=30, warmup=3)
    result.name = "creative_factory"
    return result


async def _bench_voice_runtime() -> BenchResult:
    from platform_ai.voice_engine import voice_runtime_engine

    engine = voice_runtime_engine
    if hasattr(engine, "reset"):
        engine.reset()

    def _once() -> None:
        engine.list_devices()
        engine.list_sessions(include_closed=True)

    result = _time_sync(_once, iterations=30, warmup=3)
    result.name = "voice_runtime"
    return result


async def _bench_dashboard_snapshot() -> BenchResult:
    from platform_state.cache import platform_cache

    def _work() -> None:
        platform_cache.get_or_load("dash:bench", lambda: {"widgets": 12, "ok": True})

    result = _time_sync(_work, iterations=200, warmup=10)
    result.name = "dashboard_cache_path"
    return result


async def _bench_enterprise_search() -> BenchResult:
    from platform_orchestrator.city_runtime_engine import enterprise_city_runtime_engine

    engine = enterprise_city_runtime_engine
    if hasattr(engine, "reset"):
        engine.reset()

    def _once() -> None:
        engine.search("crm", limit=20)

    result = _time_sync(_once, iterations=25, warmup=3)
    result.name = "enterprise_search"
    return result


async def _bench_concurrency() -> dict[str, Any]:
    """Concurrent AI-runtime-shaped sessions (mocked provider)."""
    from platform_ai.models import AIResponse
    from platform_ai.runtime_engine import AIRuntimeEngine
    from platform_ai import runtime_engine as re_mod

    engine = AIRuntimeEngine()
    engine.reset()

    async def fake_complete(req):
        await asyncio.sleep(0)
        return AIResponse(
            request_id=req.request_id,
            provider_id="bench",
            model_id="bench",
            content="ok",
        )

    original_complete = re_mod.ai_service.complete
    original_init = re_mod.ai_service.initialize
    re_mod.ai_service.initialize = lambda: None  # type: ignore[method-assign]
    re_mod.ai_service.complete = fake_complete  # type: ignore[method-assign]

    concurrency = 25
    started = time.perf_counter()
    try:
        await asyncio.gather(
            *[engine.execute({"prompt": f"Summarize tenant task {i}"}) for i in range(concurrency)]
        )
    finally:
        re_mod.ai_service.initialize = original_init  # type: ignore[method-assign]
        re_mod.ai_service.complete = original_complete  # type: ignore[method-assign]
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    return {
        "concurrent_sessions": concurrency,
        "total_ms": round(elapsed_ms, 2),
        "avg_ms_per_session": round(elapsed_ms / concurrency, 2),
    }


def _memory_profile(fn: Callable[[], Any]) -> dict[str, Any]:
    gc.collect()
    tracemalloc.start()
    before = tracemalloc.take_snapshot()
    fn()
    after = tracemalloc.take_snapshot()
    stats = after.compare_to(before, "lineno")
    top = [
        {
            "file": str(s.traceback[0].filename) if s.traceback else "",
            "line": s.traceback[0].lineno if s.traceback else 0,
            "size_diff_kb": round(s.size_diff / 1024, 2),
        }
        for s in stats[:5]
    ]
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {
        "current_kb": round(current / 1024, 2),
        "peak_kb": round(peak / 1024, 2),
        "top_diffs": top,
    }


async def _db_latency() -> dict[str, Any]:
    try:
        from database.session import get_session
        from sqlalchemy import text
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}

    samples: list[float] = []
    try:
        for _ in range(8):
            t0 = time.perf_counter()
            async with get_session() as session:
                await session.execute(text("SELECT 1"))
            samples.append((time.perf_counter() - t0) * 1000.0)
        from database.engine import pool_diagnostics

        return {
            "ok": True,
            "p50_ms": round(_percentile(samples, 0.50), 3),
            "p95_ms": round(_percentile(samples, 0.95), 3),
            "pool": pool_diagnostics(),
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc), "samples": samples}


async def _redis_latency() -> dict[str, Any]:
    url = os.getenv("REDIS_URL", "")
    if not url:
        try:
            from platform_configuration.configuration_center import configuration_center

            url = configuration_center.settings.redis.url or ""
        except Exception:  # noqa: BLE001
            url = ""
    if not url:
        return {"ok": False, "error": "REDIS_URL unset", "skipped": True}
    try:
        from redis.asyncio import Redis
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}

    samples: list[float] = []
    client = Redis.from_url(url, socket_connect_timeout=1.0, socket_timeout=1.0)
    try:
        for _ in range(10):
            t0 = time.perf_counter()
            await client.ping()
            samples.append((time.perf_counter() - t0) * 1000.0)
        return {
            "ok": True,
            "p50_ms": round(_percentile(samples, 0.50), 3),
            "p95_ms": round(_percentile(samples, 0.95), 3),
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}
    finally:
        await client.aclose()


class MeasuredWorkloadBench:
    """Canonical Sprint 37.3 measured harness."""

    async def run_full(self) -> dict[str, Any]:
        benches = [
            await _bench_event_loop_lag(),
            await _bench_cache(),
            await _bench_pagination(),
            await _bench_permission_engine(),
            await _bench_ai_runtime_guard(),
            await _bench_ai_runtime_execute(),
            await _bench_workflow_task_queue(),
            await _bench_multi_agent_plan(),
            await _bench_event_bus_inprocess(),
            await _bench_memory_search(),
            await _bench_knowledge_search(),
            await _bench_creative_factory(),
            await _bench_voice_runtime(),
            await _bench_dashboard_snapshot(),
            await _bench_enterprise_search(),
        ]
        concurrency = await _bench_concurrency()

        def _alloc_stress() -> None:
            buf = []
            for i in range(2000):
                buf.append({"i": i, "payload": "x" * 64})
            del buf

        memory = _memory_profile(_alloc_stress)
        db = await _db_latency()
        redis = await _redis_latency()

        by_name = {b.name: b.to_dict() for b in benches}
        api_proxy_p95 = by_name.get("permission_engine", {}).get("p95_ms", 0.0)
        critical = []
        lag = by_name.get("event_loop_lag", {})
        if lag.get("p95_ms", 0) > 25:
            critical.append("event_loop_lag_p95")
        if by_name.get("ai_runtime_execute", {}).get("errors", 0) > 0:
            critical.append("ai_runtime_errors")

        return {
            "sprint": "37.3",
            "mode": "measured",
            "benches": [b.to_dict() for b in benches],
            "by_name": by_name,
            "concurrency": concurrency,
            "memory_profile": memory,
            "db": db,
            "redis": redis,
            "api_p95_proxy_ms": api_proxy_p95,
            "critical_bottlenecks": critical,
            "passed": len(critical) == 0,
            "resource": {
                "cpu_count": os.cpu_count(),
                "pid": os.getpid(),
            },
        }


measured_workload_bench = MeasuredWorkloadBench()
