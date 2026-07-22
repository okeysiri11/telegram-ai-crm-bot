# Operations hub — aggregates fleet ops metrics and AI ops entrypoints.

from __future__ import annotations

from typing import Any

from applications.auto_marketplace.ai_operations.engine import AIOperationsEngine, ai_operations_engine
from applications.auto_marketplace.dispatch.fleet_engine import FleetDispatchEngine, fleet_dispatch_engine
from applications.auto_marketplace.executive.engine import ExecutiveDashboardEngine, executive_dashboard_engine
from applications.auto_marketplace.telematics.engine import TelematicsEngine, telematics_engine


class OperationsEngine:
    def __init__(
        self,
        dispatch: FleetDispatchEngine | None = None,
        telematics: TelematicsEngine | None = None,
        ai: AIOperationsEngine | None = None,
        executive: ExecutiveDashboardEngine | None = None,
    ) -> None:
        self.dispatch = dispatch or fleet_dispatch_engine
        self.telematics = telematics or telematics_engine
        self.ai = ai or ai_operations_engine
        self.executive = executive or executive_dashboard_engine

    def overview(self) -> dict[str, Any]:
        return {
            "dispatch": self.dispatch.metrics(),
            "telematics": self.telematics.metrics(),
            "executive": self.executive.kpis(),
            "ai": self.ai.metrics(),
        }

    def metrics(self) -> dict[str, Any]:
        return self.overview()


operations_engine = OperationsEngine()
