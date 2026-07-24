"""Strategy Dashboard — Sprint 24.7."""

from __future__ import annotations

from typing import Any


class StrategyDashboard:
    def render(
        self,
        *,
        strategy: dict[str, Any] | None = None,
        deviations: list[dict[str, Any]] | None = None,
        kpi_forecast: dict[str, Any] | None = None,
        ai_recommendations: list[str] | None = None,
        alternatives: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        strategy = dict(strategy or {})
        return {
            "current_strategy_state": strategy.get("status", "draft"),
            "strategy": strategy,
            "deviations": list(deviations or []),
            "kpi_achievement_forecast": dict(kpi_forecast or {}),
            "ai_recommendations": list(ai_recommendations or []),
            "alternatives": list(alternatives or []),
            "ai_may_act": False,
            "autonomous_decide": False,
        }
