# OperationsService — public API for Operations Dashboard backend.

from __future__ import annotations

from typing import Any

from platform_operations.dashboard_service import operations_dashboard_service
from platform_operations.metrics_service import build_metrics
from platform_operations.timeline_service import audit_timeline, event_timeline


class OperationsService:
    @staticmethod
    async def get_dashboard(*, use_cache: bool = True) -> dict[str, Any]:
        payload = await operations_dashboard_service.aggregate_dashboard(use_cache=use_cache)
        return payload.to_dict()

    @staticmethod
    async def get_widget(widget_id: str, *, use_cache: bool = True) -> dict[str, Any]:
        widget = await operations_dashboard_service.fetch_widget(widget_id, use_cache=use_cache)
        return widget.to_dict()

    @staticmethod
    async def get_metrics(*, period: str = "month") -> dict[str, Any]:
        from platform_operations.metrics_service import KpiPeriod

        period_t: KpiPeriod = period if period in {"day", "week", "month"} else "month"
        return await build_metrics(period=period_t)

    @staticmethod
    async def get_event_timeline(
        *,
        event_type: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        return await event_timeline(event_type=event_type, limit=limit)

    @staticmethod
    async def get_audit_timeline(
        *,
        category: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        return await audit_timeline(category=category, limit=limit)

    @staticmethod
    async def refresh_dashboard() -> dict[str, Any]:
        await operations_dashboard_service.invalidate_cache()
        return await OperationsService.get_dashboard(use_cache=False)


operations_service = OperationsService()
