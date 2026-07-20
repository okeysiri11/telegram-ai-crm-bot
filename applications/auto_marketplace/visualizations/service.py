# Visualizations — chart data for dashboards.

from __future__ import annotations

from applications.auto_marketplace.analytics.engine import AnalyticsEngine, analytics_engine
from applications.auto_marketplace.business_intelligence.models import ChartData
from applications.auto_marketplace.kpi.service import KPIService, kpi_service


class VisualizationService:
    def __init__(self, kpi: KPIService | None = None, analytics: AnalyticsEngine | None = None) -> None:
        self._kpi = kpi or kpi_service
        self._analytics = analytics or analytics_engine

    def revenue_chart(self) -> ChartData:
        kpis = self._kpi.as_dict()
        return ChartData(
            chart_type="bar",
            title="Revenue & Profit",
            labels=["Revenue", "Profit", "Margin"],
            datasets=[{"label": "USD", "data": [kpis.get("revenue", 0), kpis.get("profit", 0), kpis.get("gross_margin", 0)]}],
        )

    def pipeline_chart(self) -> ChartData:
        sales = self._analytics.sales_analytics()
        stages = sales.get("deals_by_stage", {})
        return ChartData(
            chart_type="pie",
            title="Deal Pipeline",
            labels=list(stages.keys()),
            datasets=[{"data": list(stages.values())}],
        )

    def lead_source_chart(self) -> ChartData:
        sales = self._analytics.sales_analytics()
        sources = sales.get("leads_by_source", {})
        return ChartData(
            chart_type="doughnut",
            title="Leads by Source",
            labels=list(sources.keys()),
            datasets=[{"data": list(sources.values())}],
        )


visualization_service = VisualizationService()
