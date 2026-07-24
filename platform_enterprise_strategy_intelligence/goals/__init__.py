"""Strategic Goals Engine — Sprint 24.7."""

from __future__ import annotations

from typing import Any

from platform_enterprise_strategy_intelligence.models import GOAL_TYPES


class StrategicGoalsEngine:
    def define(self, *, goal_type: str, target_value: float, unit: str = "pct") -> dict[str, Any]:
        goal_type = (goal_type or "").lower()
        if goal_type not in GOAL_TYPES:
            raise ValueError(f"unsupported goal: {goal_type}")
        return {
            "goal_type": goal_type,
            "target_value": float(target_value),
            "unit": unit,
            "measurable": True,
            "supported_goals": list(GOAL_TYPES),
        }

    def catalog(self) -> dict[str, Any]:
        return {"goals": list(GOAL_TYPES), "count": len(GOAL_TYPES)}
