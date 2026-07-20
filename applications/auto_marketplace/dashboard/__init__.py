# Dashboard module — dealer and admin dashboard data.

from __future__ import annotations

from typing import Any

from applications.auto_marketplace.analytics.service import analytics_service
from applications.auto_marketplace.inventory.service import inventory_service


class DashboardService:
    def overview(self) -> dict[str, Any]:
        return {
            "metrics": analytics_service.dashboard_metrics(),
            "inventory": inventory_service.stock_summary(),
            "pipeline": analytics_service.sales_pipeline(),
        }


dashboard_service = DashboardService()
