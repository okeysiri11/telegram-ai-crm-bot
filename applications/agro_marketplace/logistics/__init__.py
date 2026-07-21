"""Logistics package — planning, dispatch, delivery scheduling."""

from __future__ import annotations

from typing import Any

__all__ = ["LogisticsEngine", "LogisticsService", "logistics_engine", "logistics_service"]


def __getattr__(name: str) -> Any:
    if name in {"LogisticsEngine", "logistics_engine"}:
        from applications.agro_marketplace.logistics.engine import LogisticsEngine, logistics_engine

        return LogisticsEngine if name == "LogisticsEngine" else logistics_engine
    if name in {"LogisticsService", "logistics_service"}:
        from applications.agro_marketplace.logistics.service import LogisticsService, logistics_service

        return LogisticsService if name == "LogisticsService" else logistics_service
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
