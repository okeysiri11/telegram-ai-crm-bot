# BusinessIntelligenceEngine — orchestrates analytics, forecasting suite, executive BI.

from __future__ import annotations

from typing import Any

from applications.agro_marketplace.analytics.engine import AnalyticsEngine, analytics_engine
from applications.agro_marketplace.analytics.models import DashboardKind, SimulationScenario
from applications.agro_marketplace.forecasting.engine import ForecastingEngine, forecasting_engine


class BusinessIntelligenceEngine:
    def __init__(
        self,
        analytics: AnalyticsEngine | None = None,
        forecasting: ForecastingEngine | None = None,
    ) -> None:
        self.analytics = analytics or analytics_engine
        self.forecasting = forecasting or forecasting_engine

    async def refresh_executive(self) -> dict[str, Any]:
        dashboard = await self.analytics.dashboards.executive()
        report = await self.analytics.executive.build_executive_report()
        return {"dashboard": dashboard.to_dict(), "report": report.to_dict()}

    async def forecasting_suite(
        self,
        subject: str = "maize",
        *,
        region: str = "",
    ) -> dict[str, Any]:
        results = {
            "demand": await self.forecasting.forecast_demand(subject, region=region),
            "supply": await self.forecasting.forecast_supply(subject, region=region),
            "price": await self.forecasting.forecast_price(subject, region=region),
            "harvest": await self.forecasting.forecast_harvest(subject, region=region),
            "storage": await self.forecasting.forecast_storage(subject, region=region),
            "export": await self.forecasting.forecast_export(subject, region=region),
            "revenue": await self.forecasting.forecast_revenue(subject, region=region),
            "market_trend": await self.forecasting.forecast_market_trend(subject, region=region),
        }
        return {k: v.to_dict() for k, v in results.items()}

    async def run_simulation(self, name: str, inputs: dict[str, Any]) -> dict[str, Any]:
        scenario = self.analytics.simulation.create(
            SimulationScenario(name=name, description="BI scenario", inputs=inputs)
        )
        completed = await self.analytics.simulation.run(scenario.scenario_id)
        return completed.to_dict()

    async def role_dashboard(self, kind: str, *, subject_id: str = "") -> dict[str, Any]:
        dash = await self.analytics.dashboards.build(DashboardKind(kind), subject_id=subject_id)
        return dash.to_dict()

    def health(self) -> dict[str, Any]:
        return {
            "analytics_engine": "1.0",
            "metrics": self.analytics.metrics(),
        }


business_intelligence_engine = BusinessIntelligenceEngine()
