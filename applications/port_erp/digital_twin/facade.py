# AI Operations domain facade — digital twin, executive AI, simulation, optimization.

from __future__ import annotations

from typing import Any

from applications.port_erp.alerts.engine import AlertsEngine, alerts_engine
from applications.port_erp.dashboard.engine import ExecutiveDashboardEngine, executive_dashboard_engine
from applications.port_erp.digital_twin.engine import DigitalTwinEngine, digital_twin_engine
from applications.port_erp.executive_ai.engine import (
    DecisionSupportEngine,
    ExecutiveAIEngine,
    decision_support_engine,
    executive_ai_engine,
)
from applications.port_erp.integrations.platform_bridge import PlatformBridge, platform_bridge
from applications.port_erp.operations_center.engine import OperationsCenterEngine, operations_center_engine
from applications.port_erp.optimization.engine import OptimizationEngine, optimization_engine
from applications.port_erp.prediction.engine import PredictiveAnalyticsEngine, predictive_analytics_engine
from applications.port_erp.simulation.engine import SimulationEngine, simulation_engine


class AIOperationsDomainEngine:
    """Sprint 9.6 facade — Digital Twin & Executive Control Center."""

    def __init__(
        self,
        twin: DigitalTwinEngine | None = None,
        executive: ExecutiveAIEngine | None = None,
        operations: OperationsCenterEngine | None = None,
        optimization: OptimizationEngine | None = None,
        simulation: SimulationEngine | None = None,
        prediction: PredictiveAnalyticsEngine | None = None,
        dashboard: ExecutiveDashboardEngine | None = None,
        alerts: AlertsEngine | None = None,
        decisions: DecisionSupportEngine | None = None,
        platform: PlatformBridge | None = None,
    ) -> None:
        self.twin = twin or digital_twin_engine
        self.executive = executive or executive_ai_engine
        self.operations = operations or operations_center_engine
        self.optimization = optimization or optimization_engine
        self.simulation = simulation or simulation_engine
        self.prediction = prediction or predictive_analytics_engine
        self.dashboard = dashboard or executive_dashboard_engine
        self.alerts = alerts or alerts_engine
        self.decisions = decisions or decision_support_engine
        self._platform = platform or platform_bridge

    def metrics(self) -> dict[str, Any]:
        return {
            "snapshots": len(self.twin.list_snapshots(limit=10000)),
            "alerts": len(self.alerts.list_alerts()),
            "simulations": len(self.simulation.list_runs()),
            "optimization_plans": len(self.optimization.list_plans()),
            "predictions": len(self.prediction.list_predictions()),
        }

    async def remember_snapshot(self) -> None:
        await self._platform.remember_context("ai_ops:snapshot", self.metrics())


ai_operations_domain_engine = AIOperationsDomainEngine()
