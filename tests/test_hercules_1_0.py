"""Epic Hercules 1.0 — unit / integration / smoke tests."""

from __future__ import annotations

import pytest

from platform_hercules import VERSION, hercules_runtime
from platform_hercules.cache.cache import hercules_cache
from platform_hercules.core.models import (
    ExecutionContext,
    ExecutionGraph,
    ExecutionNode,
    ExecutionPlan,
    ExecutorBackend,
    QueueKind,
    TaskLifecycle,
)
from platform_hercules.cpu.pool import cpu_pool
from platform_hercules.gpu.pool import detect_gpu_backend, gpu_pool
from platform_hercules.memory.memory import hercules_memory
from platform_hercules.metrics.metrics import hercules_metrics
from platform_hercules.orchestrator.orchestrator import hercules_orchestrator
from platform_hercules.queue.queue import hercules_queue
from platform_hercules.scheduler.scheduler import hercules_scheduler
from platform_hercules.security.security import hercules_security
from platform_hercules.workers.registry import worker_registry
from platform_hercules.integration import DOMAIN_CHANNELS, run_via_hercules


class TestCore:
    def test_version(self):
        assert VERSION == "1.0.0"
        assert hercules_runtime.VERSION == "1.0.0"

    def test_execution_graph_topo(self):
        g = ExecutionGraph()
        g.add(ExecutionNode(id="b", name="b", depends_on=("a",)))
        g.add(ExecutionNode(id="a", name="a"))
        order = [n.id for n in g.topological_order()]
        assert order.index("a") < order.index("b")

    def test_plan_from_single(self):
        plan = ExecutionPlan.from_single(
            ExecutionContext(owner_id="u1"),
            name="t",
            backend=ExecutorBackend.INTERNAL,
        )
        assert plan.graph.nodes[0].name == "t"


class TestSchedulerQueue:
    def test_priority_dequeue(self):
        hercules_scheduler.enqueue("low", queue=QueueKind.TASK, priority=9)
        hercules_scheduler.enqueue("high", queue=QueueKind.TASK, priority=1)
        first = hercules_scheduler.dequeue([QueueKind.TASK])
        assert first == "high"

    def test_queue_lanes(self):
        hercules_queue.enqueue("j1", "ai", priority=3)
        snap = hercules_queue.snapshot()
        assert "hercules_lanes" in snap


class TestGpuCpu:
    def test_detect_backend(self):
        b = detect_gpu_backend()
        assert isinstance(b, str)

    def test_gpu_reserve_release(self):
        ok = gpu_pool.try_reserve("lease-test")
        gpu_pool.release("lease-test")
        assert ok in (True, False)
        snap = gpu_pool.snapshot()
        assert "backend" in snap

    def test_cpu_pool(self):
        assert cpu_pool.acquire()
        cpu_pool.release()
        assert cpu_pool.snapshot()["cores"] >= 1


class TestWorkersMemoryCache:
    def test_workers_seeded(self):
        kinds = {w.kind for w in worker_registry.list()}
        assert "universal" in kinds
        assert "image" in kinds
        assert worker_registry.pick("llm") is not None

    def test_memory_snapshot_restore(self):
        hercules_memory.put("k1", {"x": 1}, kind="task")
        snap = hercules_memory.snapshot("sess-1")
        assert "k1" in snap
        hercules_memory.restore("sess-1")
        assert hercules_memory.get("k1") == {"x": 1}

    def test_cache_hit_miss(self):
        hercules_cache.set("prompt", "hello", {"ok": True})
        assert hercules_cache.get("prompt", "hello") == {"ok": True}
        assert hercules_cache.get("prompt", "missing") is None
        assert hercules_cache.stats()["hits"] >= 1


class TestSecurityMetrics:
    def test_rate_limit_and_audit(self):
        assert hercules_security.check_rate("actor-test-1")
        hercules_security.record("test", "actor-test-1", "detail")
        assert hercules_security.audit_tail(1)

    def test_metrics_lifecycle(self):
        hercules_metrics.on_start()
        hercules_metrics.on_success(0.01, cost=0.1)
        d = hercules_metrics.dashboard()
        assert d["finished"] >= 1


@pytest.mark.asyncio
async def test_orchestrator_internal_job():
    plan = ExecutionPlan.from_single(
        ExecutionContext(owner_id="hercules-test", channel="api"),
        name="echo",
        backend=ExecutorBackend.INTERNAL,
        queue=QueueKind.TASK,
        payload={"ping": True},
    )
    job = await hercules_orchestrator.submit(plan)
    assert job.state.lifecycle == TaskLifecycle.SUCCEEDED
    assert job.state.result


@pytest.mark.asyncio
async def test_runtime_ai_pipeline():
    job = await hercules_runtime.submit_ai(
        ExecutionContext(owner_id="hercules-ai", channel="telegram", vertical="beauty"),
        prompt="Тест Hercules AI",
        modality="text",
        vertical="beauty",
    )
    assert job.state.lifecycle in (TaskLifecycle.SUCCEEDED, TaskLifecycle.FAILED)
    st = hercules_runtime.status(job.id)
    assert st and st["id"] == job.id
    dash = hercules_runtime.dashboard()
    assert "gpu" in dash and "workers" in dash
    assert "crm" in dash["domains"]
    ru = hercules_runtime.telegram_overview_ru()
    assert "Hercules" in ru


@pytest.mark.asyncio
async def test_integration_run_via_hercules():
    assert "beauty" in DOMAIN_CHANNELS
    st = await run_via_hercules("beauty", owner_id="h-int", prompt="Пост салона", modality="text")
    assert st.get("id")


@pytest.mark.asyncio
async def test_cancel_and_retry():
    plan = ExecutionPlan.from_single(
        ExecutionContext(owner_id="hercules-retry"),
        name="x",
        backend=ExecutorBackend.INTERNAL,
    )
    job = await hercules_orchestrator.submit(plan)
    # already finished — cancel is no-op success path
    hercules_runtime.cancel(job.id)
    again = await hercules_runtime.retry(job.id)
    assert again.id != job.id or again.state.lifecycle == TaskLifecycle.SUCCEEDED


class TestApiTelegramSmoke:
    def test_register_routes_import(self):
        from platform_hercules.api.router import HERCULES_ROUTE_SPECS, register_hercules_routes

        assert any(p == "dashboard" for _, p, _ in HERCULES_ROUTE_SPECS)
        assert callable(register_hercules_routes)

    def test_telegram_catalog_hercules(self):
        from services.telegram_ai_super_app.catalog import BTN, DEVELOPER_MENU_BUTTONS
        from services.telegram_ai_super_app.keyboards import hercules_menu_keyboard

        assert BTN.HERCULES == "🟢 Hercules"
        assert any(b.label == BTN.HERCULES for b in DEVELOPER_MENU_BUTTONS)
        flat = [b.text for row in hercules_menu_keyboard().keyboard for b in row]
        assert "🖥 GPU" in flat
        assert "📦 Очереди" in flat

    def test_management_router_registers_hercules(self):
        import inspect
        from platform_management import management_router as mr

        src = inspect.getsource(mr.register_management_routes)
        assert "register_hercules_routes" in src


class TestRecoveryFailover:
    def test_telemetry_health(self):
        from platform_hercules.telemetry.telemetry import hercules_telemetry

        h = hercules_telemetry.health()
        assert h["status"] == "ok"
        hercules_telemetry.heartbeat()
        hercules_telemetry.report_crash("unit", context={"t": 1})
        assert hercules_telemetry.diagnostics()["crashes"] >= 1
