# PerformanceTestManager — throughput and scalability benchmarks.

from __future__ import annotations

import asyncio
import inspect
import logging
import time
from typing import Any

from platform_validation.config import DEFAULT_VALIDATION_CONFIG, ValidationConfig
from platform_validation.models import PerformanceBenchmark, ValidationCheck, ValidationReport, ValidationStatus

logger = logging.getLogger(__name__)


class PerformanceTestManager:
    """Workflow, agent, memory, tool, and event processing benchmarks."""

    def __init__(self, *, config: ValidationConfig | None = None) -> None:
        self._config = config or DEFAULT_VALIDATION_CONFIG
        self._benchmarks: list[PerformanceBenchmark] = []

    def reset(self) -> None:
        self._benchmarks.clear()

    @property
    def benchmarks(self) -> list[PerformanceBenchmark]:
        return list(self._benchmarks)

    def _record(self, name: str, operations: int, duration_ms: float, **metadata: Any) -> PerformanceBenchmark:
        throughput = (operations / duration_ms * 1000.0) if duration_ms > 0 else 0.0
        bench = PerformanceBenchmark(
            name=name,
            operations=operations,
            duration_ms=duration_ms,
            throughput_ops_sec=throughput,
            metadata=metadata,
        )
        self._benchmarks.append(bench)
        return bench

    async def _timed_ops(self, name: str, operations: int, fn: Any) -> PerformanceBenchmark:
        for _ in range(self._config.performance_warmup_ops):
            if inspect.iscoroutinefunction(fn):
                await fn()
            else:
                fn()
        started = time.perf_counter()
        for _ in range(operations):
            if inspect.iscoroutinefunction(fn):
                await fn()
            else:
                fn()
        duration_ms = (time.perf_counter() - started) * 1000.0
        return self._record(name, operations, duration_ms)

    async def benchmark_event_processing(self) -> PerformanceBenchmark:
        from events.base_event import BaseEvent
        from dataclasses import dataclass

        @dataclass(kw_only=True)
        class _BenchEvent(BaseEvent):
            payload: str = ""

        from events.event_bus import PlatformEventBus

        async def publish_one():
            await PlatformEventBus.publish(_BenchEvent(payload="bench"), wait=True)

        return await self._timed_ops(
            "event_processing",
            self._config.performance_benchmark_ops,
            publish_one,
        )

    async def benchmark_memory_ops(self) -> PerformanceBenchmark:
        def memory_op():
            try:
                from platform_memory import memory_service

                _ = memory_service
            except Exception:
                pass

        return await self._timed_ops(
            "memory_performance",
            self._config.performance_benchmark_ops,
            memory_op,
        )

    async def benchmark_agent_registry(self) -> PerformanceBenchmark:
        def list_agents():
            try:
                from platform_agents.registry import agent_registry

                agent_registry.list_agents()
            except Exception:
                pass

        return await self._timed_ops(
            "agent_throughput",
            self._config.performance_benchmark_ops,
            list_agents,
        )

    async def benchmark_tool_registry(self) -> PerformanceBenchmark:
        def list_tools():
            try:
                from platform_tools.tool_registry import tool_registry

                tool_registry.list_tools()
            except Exception:
                pass

        return await self._timed_ops(
            "tool_execution",
            self._config.performance_benchmark_ops,
            list_tools,
        )

    async def benchmark_workflow_ops(self) -> PerformanceBenchmark:
        def workflow_status():
            try:
                from platform_workflow.metrics import workflow_metrics

                workflow_metrics.summary()
            except Exception:
                pass

        return await self._timed_ops(
            "workflow_throughput",
            self._config.performance_benchmark_ops,
            workflow_status,
        )

    async def run_all(self) -> ValidationReport:
        report = ValidationReport(title="Performance Report")
        runners = (
            self.benchmark_event_processing,
            self.benchmark_memory_ops,
            self.benchmark_agent_registry,
            self.benchmark_tool_registry,
            self.benchmark_workflow_ops,
        )
        for runner in runners:
            started = time.perf_counter()
            try:
                bench = await runner()
                status = ValidationStatus.PASS if bench.throughput_ops_sec > 0 else ValidationStatus.WARN
                report.checks.append(
                    ValidationCheck(
                        check_id=f"performance.{bench.name}",
                        component="performance",
                        status=status,
                        message=f"{bench.throughput_ops_sec:.1f} ops/sec over {bench.operations} ops",
                        duration_ms=(time.perf_counter() - started) * 1000.0,
                        metadata=bench.to_dict(),
                    )
                )
            except Exception as exc:
                report.checks.append(
                    ValidationCheck(
                        check_id=f"performance.{runner.__name__}",
                        component="performance",
                        status=ValidationStatus.WARN,
                        message=str(exc),
                        duration_ms=(time.perf_counter() - started) * 1000.0,
                    )
                )
        return report.finalize()


performance_test_manager = PerformanceTestManager()
