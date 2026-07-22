# Simulation Engine — what-if scenarios for port disruptions.

from __future__ import annotations

from events.publisher import publish

from applications.port_erp.digital_twin.events import SimulationCompletedEvent
from applications.port_erp.digital_twin.models import SimulationRun, SimulationScenario
from applications.port_erp.shared.exceptions import ValidationError
from applications.port_erp.shared.store import PortStore, port_store


_IMPACTS = {
    SimulationScenario.STORM_DELAYS: {
        "eta_slip_hours": 18,
        "berth_idle_pct": 0.25,
        "recommendations": ["defer non-critical berthings", "increase weather buffer"],
    },
    SimulationScenario.EQUIPMENT_FAILURES: {
        "crane_capacity_loss_pct": 0.4,
        "turnaround_increase_pct": 0.35,
        "recommendations": ["activate standby RTG", "reroute yard moves"],
    },
    SimulationScenario.TRAFFIC_OVERLOAD: {
        "gate_queue_growth": 2.5,
        "truck_turn_time_min": 90,
        "recommendations": ["stagger appointments", "open overflow gate"],
    },
    SimulationScenario.TERMINAL_SHUTDOWN: {
        "capacity_loss_pct": 1.0,
        "spillover_terminals": 1,
        "recommendations": ["divert vessels", "activate contingency berths"],
    },
    SimulationScenario.BERTH_UNAVAILABLE: {
        "waiting_vessels": 3,
        "average_wait_hours": 12,
        "recommendations": ["reassign berth plan", "anchor queue management"],
    },
    SimulationScenario.CONTAINER_OVERFLOW: {
        "yard_density": 0.98,
        "dwell_hours": 72,
        "recommendations": ["force relocate", "accelerate gate-out"],
    },
    SimulationScenario.PEAK_SEASON: {
        "volume_multiplier": 1.6,
        "utilization": 0.92,
        "recommendations": ["extend shifts", "pre-position equipment"],
    },
    SimulationScenario.EMERGENCY_RESPONSE: {
        "priority_lanes": 2,
        "response_minutes": 15,
        "recommendations": ["freeze non-urgent moves", "open emergency corridor"],
    },
}


class SimulationEngine:
    def __init__(self, store: PortStore | None = None) -> None:
        self._store = store or port_store

    def scenarios(self) -> list[str]:
        return [s.value for s in SimulationScenario]

    async def run(
        self,
        scenario: SimulationScenario | str,
        *,
        name: str = "",
        parameters: dict | None = None,
    ) -> SimulationRun:
        try:
            scen = SimulationScenario(scenario) if isinstance(scenario, str) else scenario
        except ValueError as exc:
            raise ValidationError(f"unsupported scenario: {scenario}") from exc
        base = dict(_IMPACTS[scen])
        recommendations = list(base.pop("recommendations", []))
        run = SimulationRun(
            scenario=scen,
            name=name or scen.value.replace("_", " ").title(),
            parameters=dict(parameters or {}),
            impact=base,
            recommendations=recommendations,
        )
        saved = self._store.simulation_runs.save(run.run_id, run)
        await publish(
            SimulationCompletedEvent(run_id=saved.run_id, scenario=saved.scenario.value)
        )
        return saved

    def list_runs(self) -> list[SimulationRun]:
        return sorted(self._store.simulation_runs.list_all(), key=lambda r: r.created_at, reverse=True)


simulation_engine = SimulationEngine()
