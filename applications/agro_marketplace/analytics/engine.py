# AnalyticsEngine — BI facade for domain analytics, KPIs, insights, dashboards.

from __future__ import annotations

from typing import Any

from applications.agro_marketplace.analytics.ai_integration import AnalyticsAIIntegration, analytics_ai
from applications.agro_marketplace.analytics.service import AnalyticsService, analytics_service
from applications.agro_marketplace.dashboards.service import DashboardsService, dashboards_service
from applications.agro_marketplace.executive.service import ExecutiveService, executive_service
from applications.agro_marketplace.insights.service import InsightsService, insights_service
from applications.agro_marketplace.kpi.service import KPIService, kpi_service
from applications.agro_marketplace.metrics.service import MetricsService, metrics_service
from applications.agro_marketplace.reporting.service import ReportingService, reporting_service
from applications.agro_marketplace.shared.store import AgroStore, agro_store
from applications.agro_marketplace.simulation.service import SimulationService, simulation_service


class AnalyticsEngine:
    def __init__(
        self,
        store: AgroStore | None = None,
        analytics: AnalyticsService | None = None,
        kpi: KPIService | None = None,
        insights: InsightsService | None = None,
        dashboards: DashboardsService | None = None,
        reporting: ReportingService | None = None,
        executive: ExecutiveService | None = None,
        simulation: SimulationService | None = None,
        metrics_svc: MetricsService | None = None,
        ai: AnalyticsAIIntegration | None = None,
    ) -> None:
        self._store = store or agro_store
        self.analytics = analytics or analytics_service
        self.kpi = kpi or kpi_service
        self.insights = insights or insights_service
        self.dashboards = dashboards or dashboards_service
        self.reporting = reporting or reporting_service
        self.executive = executive or executive_service
        self.simulation = simulation or simulation_service
        self.metrics_svc = metrics_svc or metrics_service
        self._ai = ai or analytics_ai

    def domain(self, name: str) -> dict[str, Any]:
        return self.analytics.domain_report(name)

    def all_domains(self) -> dict[str, Any]:
        domains = [
            "sales",
            "inventory",
            "harvest",
            "crop",
            "demand",
            "supply",
            "pricing",
            "export",
            "customer",
            "regional",
        ]
        return {d: self.analytics.domain_report(d) for d in domains}

    def metrics(self) -> dict[str, Any]:
        return {
            "dashboard": self.analytics.dashboard_metrics(),
            "ai": self.analytics.ai_insights(),
            "kpis": self._store.kpi_snapshots.count(),
            "insights": self._store.insights.count(),
            "anomalies": self._store.anomalies.count(),
            "dashboards": self._store.dashboard_snapshots.count(),
            "bi_reports": self._store.bi_reports.count(),
            "simulations": self._store.simulations.count(),
            "forecasts": self._store.forecasts.count(),
        }


analytics_engine = AnalyticsEngine()
