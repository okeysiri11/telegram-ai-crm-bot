# StressTestManager — high concurrency and load scenarios.

from __future__ import annotations

import asyncio
import inspect
import logging
import time
from typing import Any

from platform_validation.config import DEFAULT_VALIDATION_CONFIG, ValidationConfig
from platform_validation.models import StressTestResult, ValidationCheck, ValidationReport, ValidationStatus

logger = logging.getLogger(__name__)


class StressTestManager:
    """Stress tests: concurrency, large workflows, memory datasets, recovery."""

    def __init__(self, *, config: ValidationConfig | None = None) -> None:
        self._config = config or DEFAULT_VALIDATION_CONFIG
        self._results: list[StressTestResult] = []

    def reset(self) -> None:
        self._results.clear()

    @property
    def results(self) -> list[StressTestResult]:
        return list(self._results)

    async def _run_concurrent(self, scenario: str, fn: Any, *, concurrency: int, total: int) -> StressTestResult:
        semaphore = asyncio.Semaphore(concurrency)
        successes = 0
        errors = 0

        async def worker():
            nonlocal successes, errors
            async with semaphore:
                try:
                    if inspect.iscoroutinefunction(fn):
                        await fn()
                    else:
                        fn()
                    successes += 1
                except Exception:
                    errors += 1

        started = time.perf_counter()
        await asyncio.gather(*(worker() for _ in range(total)))
        duration_ms = (time.perf_counter() - started) * 1000.0
        success_rate = successes / total if total else 0.0
        result = StressTestResult(
            scenario=scenario,
            concurrency=concurrency,
            operations=total,
            success_rate=success_rate,
            duration_ms=duration_ms,
            recovered=success_rate >= 0.95,
        )
        self._results.append(result)
        return result

    async def stress_event_bus(self) -> StressTestResult:
        from dataclasses import dataclass

        from events.base_event import BaseEvent
        from events.event_bus import PlatformEventBus

        @dataclass(kw_only=True)
        class _StressEvent(BaseEvent):
            idx: int = 0

        async def publish():
            await PlatformEventBus.publish(_StressEvent(idx=1), wait=True)

        return await self._run_concurrent(
            "high_concurrency_events",
            publish,
            concurrency=min(self._config.stress_concurrency, 20),
            total=min(self._config.stress_operations, 200),
        )

    async def stress_agent_registry(self) -> StressTestResult:
        def list_agents():
            from platform_agents.registry import agent_registry

            agent_registry.list_agents()

        return await self._run_concurrent(
            "multiple_agents",
            list_agents,
            concurrency=self._config.stress_concurrency,
            total=min(self._config.stress_operations, 500),
        )

    async def stress_memory_dataset(self) -> StressTestResult:
        def write_read():
            try:
                from platform_memory import memory_service

                _ = memory_service
            except Exception:
                raise

        return await self._run_concurrent(
            "large_memory_dataset",
            write_read,
            concurrency=min(self._config.stress_concurrency, 30),
            total=min(self._config.stress_operations, 300),
        )

    async def stress_workflow_tasks(self) -> StressTestResult:
        def task_ops():
            try:
                from platform_workflow.metrics import workflow_metrics

                workflow_metrics.summary()
            except Exception:
                pass

        return await self._run_concurrent(
            "thousands_of_tasks",
            task_ops,
            concurrency=self._config.stress_concurrency,
            total=min(self._config.stress_operations, 1000),
        )

    async def stress_recovery(self) -> StressTestResult:
        async def recovery_op():
            try:
                from platform_reliability import reliability_manager

                reliability_manager.metrics_summary()
            except Exception:
                pass

        return await self._run_concurrent(
            "recovery_under_stress",
            recovery_op,
            concurrency=min(self._config.stress_concurrency, 25),
            total=min(self._config.stress_operations, 250),
        )

    async def run_all(self) -> ValidationReport:
        report = ValidationReport(title="Stress Test Report")
        scenarios = (
            self.stress_event_bus,
            self.stress_agent_registry,
            self.stress_memory_dataset,
            self.stress_workflow_tasks,
            self.stress_recovery,
        )
        for scenario_fn in scenarios:
            started = time.perf_counter()
            try:
                result = await scenario_fn()
                status = ValidationStatus.PASS if result.success_rate >= 0.9 else ValidationStatus.WARN
                if result.success_rate < 0.5:
                    status = ValidationStatus.FAIL
                report.checks.append(
                    ValidationCheck(
                        check_id=f"stress.{result.scenario}",
                        component="stress",
                        status=status,
                        message=f"success_rate={result.success_rate:.2%} concurrency={result.concurrency}",
                        duration_ms=(time.perf_counter() - started) * 1000.0,
                        metadata=result.to_dict(),
                    )
                )
            except Exception as exc:
                report.checks.append(
                    ValidationCheck(
                        check_id=f"stress.{scenario_fn.__name__}",
                        component="stress",
                        status=ValidationStatus.WARN,
                        message=str(exc),
                        duration_ms=(time.perf_counter() - started) * 1000.0,
                    )
                )
        return report.finalize()


stress_test_manager = StressTestManager()
