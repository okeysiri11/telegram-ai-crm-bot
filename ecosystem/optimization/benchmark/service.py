# Benchmark suite — compare current performance to baselines.

from __future__ import annotations

from typing import Any

from ecosystem.optimization.models import BenchmarkResult
from ecosystem.shared.store import EcosystemStore, ecosystem_store


class BenchmarkService:
    BASELINES = {
        "success_rate": 0.95,
        "avg_latency_ms": 200.0,
        "task_completion": 10.0,
        "agent_utilization": 0.6,
    }

    def __init__(self, store: EcosystemStore | None = None) -> None:
        self._store = store or ecosystem_store

    def run_suite(self) -> list[BenchmarkResult]:
        from ecosystem.optimization.continuous_learning.service import continuous_learning

        analysis = continuous_learning.analyze_history()
        results = []
        results.append(
            self._benchmark("success_rate", analysis["success_rate"] or 1.0, self.BASELINES["success_rate"])
        )
        results.append(
            self._benchmark(
                "avg_latency_ms",
                analysis["avg_latency_ms"] or 50.0,
                self.BASELINES["avg_latency_ms"],
                lower_is_better=True,
            )
        )
        completed = len([t for t in self._store.workforce_tasks.list_all() if t.status.value == "completed"])
        results.append(self._benchmark("task_completion", float(completed), self.BASELINES["task_completion"]))
        specialists = self._store.specialists.list_all()
        util = (
            sum(s.active_tasks for s in specialists) / sum(s.max_tasks for s in specialists)
            if specialists and sum(s.max_tasks for s in specialists)
            else 0.0
        )
        results.append(self._benchmark("agent_utilization", util, self.BASELINES["agent_utilization"]))
        return results

    def _benchmark(
        self,
        name: str,
        score: float,
        baseline: float,
        *,
        lower_is_better: bool = False,
        details: dict[str, Any] | None = None,
    ) -> BenchmarkResult:
        delta = baseline - score if lower_is_better else score - baseline
        result = BenchmarkResult(
            name=name,
            score=round(score, 4),
            baseline=baseline,
            delta=round(delta, 4),
            details=details or {"lower_is_better": lower_is_better},
        )
        self._store.benchmark_results.save(result.benchmark_id, result)
        return result

    def list_results(self) -> list[BenchmarkResult]:
        return sorted(self._store.benchmark_results.list_all(), key=lambda b: b.created_at, reverse=True)


benchmark_service = BenchmarkService()
