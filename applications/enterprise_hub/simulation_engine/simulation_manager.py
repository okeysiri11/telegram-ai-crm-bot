from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"



from applications.enterprise_hub.simulation_engine.decision_engine import DecisionEngine
from applications.enterprise_hub.simulation_engine.forecasting_engine import ForecastingEngine
from applications.enterprise_hub.simulation_engine.monte_carlo import MonteCarloSimulation
from applications.enterprise_hub.simulation_engine.optimization.engine import OptimizationEngine
from applications.enterprise_hub.simulation_engine.risk_engine import RiskEngine
from applications.enterprise_hub.simulation_engine.scenario_engine import ScenarioEngine
from applications.enterprise_hub.simulation_engine.sensitivity_analysis import SensitivityAnalysis
from applications.enterprise_hub.simulation_engine.simulation_history import SimulationHistory
from applications.enterprise_hub.simulation_engine.simulation_scheduler import SimulationScheduler


class SimulationManager:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.scenarios = ScenarioEngine(self.store)
        self.decisions = DecisionEngine(self.store)
        self.forecasts = ForecastingEngine(self.store)
        self.optimization = OptimizationEngine(self.store)
        self.risks = RiskEngine(self.store)
        self.monte_carlo = MonteCarloSimulation(self.store)
        self.sensitivity = SensitivityAnalysis(self.store)
        self.scheduler = SimulationScheduler(self.store)
        self.history = SimulationHistory(self.store)

    def status(self) -> dict[str, Any]:
        return {
            "scenarios": self.scenarios.status(),
            "decisions": self.decisions.status(),
            "forecasts": self.forecasts.status(),
            "optimization": self.optimization.status(),
            "risks": self.risks.status(),
            "monte_carlo": self.monte_carlo.status(),
            "sensitivity": self.sensitivity.status(),
            "scheduler": self.scheduler.status(),
            "history": self.history.status(),
        }
