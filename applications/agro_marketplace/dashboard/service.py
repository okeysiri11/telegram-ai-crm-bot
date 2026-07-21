# DashboardService — consolidated agro marketplace dashboard.

from __future__ import annotations

from typing import Any

from applications.agro_marketplace.analytics.service import AnalyticsService, analytics_service


class DashboardService:
    def __init__(self, analytics: AnalyticsService | None = None) -> None:
        self._analytics = analytics or analytics_service

    def overview(self) -> dict[str, Any]:
        metrics = self._analytics.dashboard_metrics()
        return {
            "title": "Agro Marketplace Dashboard",
            "metrics": metrics,
            "orders_by_status": self._analytics.orders_by_status(),
        }


dashboard_service = DashboardService()
