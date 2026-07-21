# Simulation engine — what-if, business, agent, workflow, risk, capacity.

from __future__ import annotations

from typing import Any

from events.publisher import publish

from ecosystem.optimization.events import SimulationCompletedEvent
from ecosystem.optimization.models import SimulationRun, SimulationType
from ecosystem.shared.exceptions import ValidationError
from ecosystem.shared.store import EcosystemStore, ecosystem_store


class SimulationEngine:
    def __init__(self, store: EcosystemStore | None = None) -> None:
        self._store = store or ecosystem_store

    async def run(
        self,
        name: str,
        simulation_type: SimulationType,
        assumptions: dict[str, Any],
    ) -> SimulationRun:
        if not name:
            raise ValidationError("name is required")
        results, risk = self._simulate(simulation_type, assumptions)
        run = SimulationRun(
            simulation_type=simulation_type,
            name=name,
            assumptions=assumptions,
            results=results,
            risk_score=risk,
        )
        self._store.simulation_runs.save(run.simulation_id, run)
        await publish(
            SimulationCompletedEvent(
                simulation_id=run.simulation_id,
                simulation_type=simulation_type.value,
                risk_score=risk,
            )
        )
        return run

    def _simulate(self, simulation_type: SimulationType, assumptions: dict[str, Any]) -> tuple[dict[str, Any], float]:
        load = float(assumptions.get("load_factor", 1.0))
        budget = float(assumptions.get("budget", 10000))
        agents = int(assumptions.get("agents", 8))
        capacity = float(assumptions.get("capacity", 100))

        if simulation_type == SimulationType.WHAT_IF:
            projected = capacity * load
            risk = min(1.0, max(0.0, (projected - capacity) / capacity)) if capacity else 0.5
            return {"projected_load": projected, "feasible": projected <= capacity * 1.2}, risk

        if simulation_type == SimulationType.BUSINESS:
            revenue = budget * 1.4 * load
            margin = max(0.05, 0.35 - (load - 1) * 0.05)
            risk = 0.3 if load > 1.5 else 0.15
            return {"projected_revenue": round(revenue, 2), "margin": round(margin, 3)}, risk

        if simulation_type == SimulationType.AGENT_STRATEGY:
            throughput = agents * 12 / max(load, 0.1)
            risk = 0.4 if agents < 4 else 0.2
            return {"throughput_per_day": round(throughput, 1), "agents": agents}, risk

        if simulation_type == SimulationType.WORKFLOW:
            steps = int(assumptions.get("steps", 5))
            latency = steps * 40 * load
            risk = min(1.0, latency / 1000)
            return {"estimated_latency_ms": round(latency, 1), "steps": steps}, risk

        if simulation_type == SimulationType.RISK:
            failure_rate = float(assumptions.get("failure_rate", 0.05)) * load
            risk = min(1.0, failure_rate * 5)
            return {"projected_failure_rate": round(failure_rate, 4), "mitigations": ["retry", "fallback", "escalate"]}, risk

        # CAPACITY
        headroom = capacity - capacity * load
        risk = 0.1 if headroom > 20 else 0.55
        return {"headroom": round(headroom, 1), "scale_recommended": headroom < 20}, risk

    def list_runs(self, *, simulation_type: SimulationType | None = None) -> list[SimulationRun]:
        runs = self._store.simulation_runs.list_all()
        if simulation_type:
            runs = [r for r in runs if r.simulation_type == simulation_type]
        return sorted(runs, key=lambda r: r.created_at, reverse=True)


simulation_engine = SimulationEngine()
