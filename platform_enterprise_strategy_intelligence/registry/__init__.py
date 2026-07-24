"""Strategy Registry — Sprint 24.7."""

from __future__ import annotations

from typing import Any

from platform_enterprise_strategy_intelligence.models import STRATEGY_STATUSES


class StrategyRegistry:
    def create(
        self,
        *,
        strategy_id: str,
        name: str,
        goal: str,
        horizon: str = "year",
        owner: str = "platform_owner",
        kpis: dict[str, Any] | None = None,
        version: str = "1.0",
    ) -> dict[str, Any]:
        if not strategy_id or not name:
            raise ValueError("strategy_id and name are required")
        return {
            "strategy_id": strategy_id,
            "name": name.strip(),
            "goal": goal.strip(),
            "planning_horizon": horizon,
            "responsible": owner,
            "status": "draft",
            "kpi": dict(kpis or {}),
            "version": version,
            "change_history": [],
        }

    def set_status(self, strategy: dict[str, Any], *, status: str) -> dict[str, Any]:
        status = (status or "").lower()
        if status not in STRATEGY_STATUSES:
            raise ValueError(f"unsupported status: {status}")
        updated = dict(strategy)
        updated["status"] = status
        return updated

    def record_change(self, strategy: dict[str, Any], *, note: str, actor: str = "system") -> dict[str, Any]:
        updated = dict(strategy)
        hist = list(updated.get("change_history") or [])
        hist.append({"note": note, "actor": actor})
        updated["change_history"] = hist[-50:]
        return updated
