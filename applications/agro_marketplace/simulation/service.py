# Scenario simulation for executive what-if analysis.

from __future__ import annotations

import time

from events.publisher import publish

from applications.agro_marketplace.analytics.ai_integration import AnalyticsAIIntegration, analytics_ai
from applications.agro_marketplace.analytics.events import SimulationCompletedEvent
from applications.agro_marketplace.analytics.models import SimulationScenario
from applications.agro_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class SimulationService:
    def __init__(
        self,
        store: AgroStore | None = None,
        ai: AnalyticsAIIntegration | None = None,
    ) -> None:
        self._store = store or agro_store
        self._ai = ai or analytics_ai

    def create(self, scenario: SimulationScenario) -> SimulationScenario:
        if not scenario.name:
            raise ValidationError("name is required")
        scenario.status = "draft"
        return self._store.simulations.save(scenario.scenario_id, scenario)

    def get(self, scenario_id: str) -> SimulationScenario:
        scenario = self._store.simulations.get(scenario_id)
        if scenario is None:
            raise NotFoundError("SimulationScenario", scenario_id)
        return scenario

    def list_scenarios(self) -> list[SimulationScenario]:
        return self._store.simulations.list_all()

    async def run(self, scenario_id: str) -> SimulationScenario:
        scenario = self.get(scenario_id)
        results = await self._ai.run_scenario(scenario.name, scenario.inputs)
        scenario.results = results
        scenario.status = "completed"
        scenario.completed_at = time.time()
        saved = self._store.simulations.save(scenario_id, scenario)
        await publish(
            SimulationCompletedEvent(
                scenario_id=saved.scenario_id,
                name=saved.name,
                status=saved.status,
            )
        )
        return saved


simulation_service = SimulationService()
