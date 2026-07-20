# BIEngine — unified Business Intelligence & Executive Dashboard facade.

from __future__ import annotations

from typing import Any

from applications.auto_marketplace.analytics.engine import AnalyticsEngine, analytics_engine
from applications.auto_marketplace.business_intelligence.ai_insights import AIInsightsService, ai_insights_service
from applications.auto_marketplace.business_intelligence.security import BISecurity, bi_security
from applications.auto_marketplace.executive_dashboard.service import ExecutiveDashboardService, executive_dashboard_service
from applications.auto_marketplace.forecasting.service import ForecastingService, forecasting_service
from applications.auto_marketplace.kpi.service import KPIService, kpi_service
from applications.auto_marketplace.reports.bi_service import BIReportService, bi_report_service
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store
from applications.auto_marketplace.statistics.service import StatisticsService, statistics_service
from applications.auto_marketplace.visualizations.service import VisualizationService, visualization_service


class BIEngine:
    """Enterprise Business Intelligence & Executive Dashboard entry point."""

    def __init__(
        self,
        store: MarketplaceStore | None = None,
        dashboard: ExecutiveDashboardService | None = None,
        analytics: AnalyticsEngine | None = None,
        kpi: KPIService | None = None,
        forecasting: ForecastingService | None = None,
        reports: BIReportService | None = None,
        statistics: StatisticsService | None = None,
        visualizations: VisualizationService | None = None,
        insights: AIInsightsService | None = None,
        security: BISecurity | None = None,
    ) -> None:
        self._store = store or marketplace_store
        self.dashboard = dashboard or executive_dashboard_service
        self.analytics = analytics or analytics_engine
        self.kpi = kpi or kpi_service
        self.forecasting = forecasting or forecasting_service
        self.reports = reports or bi_report_service
        self.statistics = statistics or statistics_service
        self.visualizations = visualizations or visualization_service
        self.insights = insights or ai_insights_service
        self.security = security or bi_security

    def metrics(self) -> dict[str, Any]:
        return {
            "dashboards": self._store.bi_dashboards.count(),
            "reports": self._store.bi_reports.count(),
            "forecasts": self._store.bi_forecasts.count(),
            "insights": self._store.bi_insights.count(),
            "kpis": len(self.kpi.compute_all()),
        }


bi_engine = BIEngine()
