# Optimization engine — orchestrates learning, performance, simulation, recommendations.

from __future__ import annotations

from typing import Any

from events.publisher import publish

from ecosystem.config import DEFAULT_CONFIG
from ecosystem.optimization.benchmark.service import BenchmarkService, benchmark_service
from ecosystem.optimization.continuous_learning.service import ContinuousLearningService, continuous_learning
from ecosystem.optimization.events import OptimizationStartedEvent
from ecosystem.optimization.feedback.service import FeedbackService, feedback_service
from ecosystem.optimization.models import OptimizationRun, SimulationType
from ecosystem.optimization.performance.service import PerformanceEngine, performance_engine
from ecosystem.optimization.recommendations.service import RecommendationEngine, recommendation_engine
from ecosystem.optimization.simulation.service import SimulationEngine, simulation_engine
from ecosystem.optimization.strategy.service import StrategyService, strategy_service
from ecosystem.shared.store import EcosystemStore, ecosystem_store


class OptimizationEngine:
    """Continuous learning and ecosystem optimization facade."""

    def __init__(
        self,
        store: EcosystemStore | None = None,
        learning: ContinuousLearningService | None = None,
        performance: PerformanceEngine | None = None,
        feedback: FeedbackService | None = None,
        simulation: SimulationEngine | None = None,
        benchmark: BenchmarkService | None = None,
        recommendations: RecommendationEngine | None = None,
        strategy: StrategyService | None = None,
    ) -> None:
        self._store = store or ecosystem_store
        self.learning = learning or continuous_learning
        self.performance = performance or performance_engine
        self.feedback = feedback or feedback_service
        self.simulation = simulation or simulation_engine
        self.benchmark = benchmark or benchmark_service
        self.recommendations = recommendations or recommendation_engine
        self.strategy = strategy or strategy_service

    async def optimize(self, *, scope: str = "ecosystem") -> dict[str, Any]:
        run = OptimizationRun(status="running", summary="")
        self._store.optimization_runs.save(run.run_id, run)
        await publish(OptimizationStartedEvent(run_id=run.run_id, scope=scope))

        # Collect telemetry from ecosystem subsystems
        self.learning.record_execution("optimization", "optimize_started", application_id="ecosystem", duration_ms=5)
        await self.performance.collect_ecosystem_metrics()
        cycle = await self.learning.run_learning_cycle()
        recs = await self.recommendations.generate(force=True)
        sim = await self.simulation.run(
            "Capacity check",
            SimulationType.CAPACITY,
            {"load_factor": 1.2, "capacity": 100},
        )
        strategy = await self.strategy.update_from_recommendations(
            f"Optimization cycle {run.run_id[:8]}",
            recommendation_ids=[r.recommendation_id for r in recs[:3]],
        )
        benches = self.benchmark.run_suite()

        # Optional bridges to assistant / workforce / communication
        integrations = await self._integrate_ai()

        run.status = "completed"
        run.learning_cycle_id = cycle.cycle_id
        run.recommendation_ids = [r.recommendation_id for r in recs]
        run.simulation_ids = [sim.simulation_id]
        run.summary = f"Analyzed {cycle.records_analyzed} records; {len(recs)} recommendations; strategy {strategy.strategy_id}"
        self._store.optimization_runs.save(run.run_id, run)

        return {
            "run": run.to_dict(),
            "learning_cycle": cycle.to_dict(),
            "recommendations": [r.to_dict() for r in recs],
            "simulation": sim.to_dict(),
            "strategy": strategy.to_dict(),
            "benchmarks": [b.to_dict() for b in benches],
            "integrations": integrations,
        }

    async def _integrate_ai(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "learning": True,
            "reasoning": False,
            "planning": False,
            "decision": False,
            "collaboration": False,
            "knowledge": False,
            "executive": False,
        }
        try:
            from ecosystem.assistant.knowledge_graph.service import knowledge_graph

            await knowledge_graph.upsert_node(
                "Optimization Run",
                "Ecosystem optimization cycle completed",
                tags=["optimization"],
            )
            result["knowledge"] = True
        except Exception:
            pass
        try:
            from ecosystem.workforce.executive.service import executive_service
            from ecosystem.workforce.models import ExecutiveRole

            await executive_service.decide(
                ExecutiveRole.CAO,
                "Acknowledge optimization cycle",
                rationale="Analytics AI reviewed learning insights",
            )
            result["executive"] = True
            result["decision"] = True
        except Exception:
            pass
        try:
            from ecosystem.workforce.coordination.service import coordination_service

            await coordination_service.collaborate(
                "Optimization alignment",
                ["operations", "development"],
                shared_memory={"topic": "optimization"},
            )
            result["collaboration"] = True
            result["planning"] = True
        except Exception:
            pass
        try:
            from ecosystem.integrations.platform_bridge import platform_bridge

            await platform_bridge.delegate_task("ecosystem_optimize", {"scope": "full"})
            result["reasoning"] = True
        except Exception:
            pass
        return result

    def metrics(self) -> dict[str, Any]:
        return {
            "ecosystem_version": DEFAULT_CONFIG.ecosystem_version,
            "optimization_layer": DEFAULT_CONFIG.optimization_layer,
            "continuous_learning": DEFAULT_CONFIG.continuous_learning,
            "execution_records": self._store.execution_records.count(),
            "learning_cycles": self._store.learning_cycles.count(),
            "recommendations": self._store.recommendations.count(),
            "simulations": self._store.simulation_runs.count(),
            "performance_snapshots": self._store.performance_snapshots.count(),
            "strategies": self._store.strategy_updates.count(),
            "optimization_runs": self._store.optimization_runs.count(),
        }


optimization_engine = OptimizationEngine()
