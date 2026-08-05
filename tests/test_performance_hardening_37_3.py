"""Sprint 37.3 — Enterprise Performance & Scalability tests.

Measured workload harness, pool tuning, cache hit-rate wiring, startup timing.
No API/business-logic contract changes.
"""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_pool_settings_env_tunable():
    from platform_configuration.settings import DatabaseSettings

    s = DatabaseSettings(pool_size=32, max_overflow=64, pool_timeout=15.0, pool_recycle=900)
    assert s.pool_size == 32
    assert s.max_overflow == 64
    assert s.pool_recycle == 900


def test_engine_pool_kwargs_defaults():
    from database.engine import _pool_kwargs

    cfg = _pool_kwargs()
    assert cfg["pool_size"] >= 1
    assert cfg["max_overflow"] >= 0
    assert cfg["pool_recycle"] > 0


def test_cache_hit_rate_wired():
    from platform_state.cache import platform_cache
    from platform_state.telemetry import enterprise_telemetry

    enterprise_telemetry.reset()
    platform_cache.reset()
    platform_cache.queries.set("a", 1)
    assert platform_cache.queries.get("a") == 1
    assert platform_cache.queries.get("missing") is None
    rate = enterprise_telemetry.cache_hit_rate()
    assert 0.0 <= rate <= 1.0
    snap = enterprise_telemetry.snapshot()
    assert "cache_hit_rate" in snap
    assert "cache_hit_rate" in snap["tracks"]


def test_startup_timing_instrumented_in_source():
    src = (ROOT / "startup.py").read_text(encoding="utf-8")
    assert "phases_ms" in src
    assert "startup_timing" in src
    assert "graceful_shutdown_ms" in src


def test_pagination_bounds():
    from platform_api.pagination import PaginationParams

    p = PaginationParams.from_query({"page": "1", "page_size": "9999"})
    assert p.page_size == 500
    assert p.offset == 0


@pytest.mark.asyncio
async def test_measured_workload_suite():
    from platform_performance.measured_workload import measured_workload_bench

    report = await measured_workload_bench.run_full()
    assert report["sprint"] == "37.3"
    assert report["mode"] == "measured"
    assert report["passed"] is True
    assert not report["critical_bottlenecks"]

    by_name = report["by_name"]
    for required in (
        "event_loop_lag",
        "platform_cache_lru",
        "permission_engine",
        "ai_runtime_execute",
        "workflow_task_queue",
        "multi_agent_plan",
        "event_bus_inprocess",
        "enterprise_search",
    ):
        assert required in by_name, required
        assert by_name[required]["iterations"] > 0
        # Soft budgets — catch regressions without flaking on CI hosts
        assert by_name[required]["p95_ms"] < 5000, required

    assert report["concurrency"]["concurrent_sessions"] >= 10
    assert "memory_profile" in report
    assert "db" in report
    assert "redis" in report


@pytest.mark.asyncio
async def test_load_stress_endurance_slices():
    """Concurrency + repeated loops approximate load/stress/endurance without external tools."""
    from platform_performance.measured_workload import (
        _bench_concurrency,
        _bench_event_loop_lag,
        _bench_permission_engine,
    )

    # load
    load = await _bench_concurrency()
    assert load["concurrent_sessions"] == 25

    # stress — elevated loop samples
    lag = await _bench_event_loop_lag(samples=80)
    assert lag.p95_ms < 50

    # endurance — many sync iterations
    perm = await _bench_permission_engine()
    assert perm.iterations >= 100
    assert perm.errors == 0


def test_measured_module_exported_path():
    path = ROOT / "platform_performance" / "measured_workload.py"
    assert path.is_file()
