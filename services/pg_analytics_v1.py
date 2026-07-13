# Analytics Engine v1 — product layer.

from __future__ import annotations

import uuid
from typing import Any

from services.pg_analytics_engine import AnalyticsEngineError, AnalyticsEngineV1

ANALYTICS_FEATURES = frozenset({
    "daily_aggregation",
    "dashboard",
    "export_reports",
})


class AnalyticsProductError(Exception):
    pass


class AnalyticsV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        return await AnalyticsEngineV1.user_can_access(user_id)

    @staticmethod
    def list_features() -> list[dict[str, str]]:
        labels = {
            "daily_aggregation": "Daily Aggregation",
            "dashboard": "Dashboard API",
            "export_reports": "Export Reports",
        }
        return [{"code": k, "label": labels[k]} for k in sorted(ANALYTICS_FEATURES)]

    @staticmethod
    async def _wrap(coro):
        try:
            return await coro
        except AnalyticsEngineError as exc:
            raise AnalyticsProductError(str(exc)) from exc

    @staticmethod
    async def get_analytics(actor_id: int, tenant_id: uuid.UUID) -> dict[str, Any]:
        dashboard = await AnalyticsV1._wrap(
            AnalyticsEngineV1.get_dashboard(actor_id, tenant_id)
        )
        return {
            **dashboard,
            "features": list(ANALYTICS_FEATURES),
            "metrics": [
                "CPL",
                "CAC",
                "Conversion Rate",
                "Average Deal Size",
                "Lead Source ROI",
                "Manager Performance",
                "Vehicle Turnover",
            ],
        }

    @staticmethod
    async def get_feature(
        actor_id: int,
        tenant_id: uuid.UUID,
        feature: str,
        *,
        export_format: str = "json",
    ) -> dict[str, Any]:
        if feature not in ANALYTICS_FEATURES:
            raise AnalyticsProductError(f"Unknown feature: {feature}")

        if feature == "daily_aggregation":
            result = await AnalyticsV1._wrap(
                AnalyticsEngineV1.aggregate_daily(actor_id, tenant_id)
            )
            return {"feature": feature, **result}

        if feature == "dashboard":
            result = await AnalyticsV1._wrap(
                AnalyticsEngineV1.get_dashboard(actor_id, tenant_id)
            )
            return {"feature": feature, **result}

        if feature == "export_reports":
            result = await AnalyticsV1._wrap(
                AnalyticsEngineV1.export_report(
                    actor_id, tenant_id, format=export_format
                )
            )
            return {"feature": feature, **result}

        return {"feature": feature, "status": "available"}
