"""Analytics package — domain metrics and AnalyticsEngine."""

from __future__ import annotations

from typing import Any

__all__ = ["AnalyticsEngine", "AnalyticsService", "analytics_engine", "analytics_service"]


def __getattr__(name: str) -> Any:
    if name in {"AnalyticsEngine", "analytics_engine"}:
        from applications.agro_marketplace.analytics.engine import AnalyticsEngine, analytics_engine

        return AnalyticsEngine if name == "AnalyticsEngine" else analytics_engine
    if name in {"AnalyticsService", "analytics_service"}:
        from applications.agro_marketplace.analytics.service import AnalyticsService, analytics_service

        return AnalyticsService if name == "AnalyticsService" else analytics_service
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
