"""Autonomous planning, predictive intelligence, optimization, executive AI."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.agro_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.agro_enterprise.shared.store import AgroEnterpriseStore, agro_enterprise_store

PLAN_TYPES = [
    "season",
    "field_work",
    "machinery",
    "drone",
    "irrigation",
    "fertilization",
    "harvest",
    "workforce",
]
FORECAST_TYPES = [
    "yield",
    "weather_impact",
    "disease",
    "market",
    "resource_demand",
    "financial",
    "supply_chain",
]
OPT_TYPES = [
    "resource",
    "equipment",
    "labor",
    "fuel",
    "inventory",
    "water",
    "energy",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AutonomousPlanning:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store

    def create_plan(
        self,
        *,
        plan_type: str,
        farm_id: str,
        title: str,
        window_start: str = "",
        window_end: str = "",
        assets: list[str] | None = None,
    ) -> dict[str, Any]:
        if plan_type not in PLAN_TYPES:
            raise ValidationError(f"plan_type must be one of {PLAN_TYPES}")
        if not title:
            raise ValidationError("title required")
        pid = _id("aa_plan")
        return self.store.aa_plans.save(
            pid,
            {
                "plan_id": pid,
                "plan_type": plan_type,
                "farm_id": farm_id,
                "title": title,
                "window_start": window_start,
                "window_end": window_end,
                "assets": assets or [],
                "status": "scheduled",
                "autonomous": True,
                "at": _now(),
            },
        )

    def activate(self, plan_id: str) -> dict[str, Any]:
        plan = self.store.aa_plans.get(plan_id)
        if plan is None:
            raise NotFoundError("plan", plan_id)
        plan["status"] = "active"
        plan["activated_at"] = _now()
        return self.store.aa_plans.save(plan_id, plan)

    def status(self) -> dict[str, Any]:
        return {"plans": self.store.aa_plans.count()}


class PredictiveIntelligence:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store

    def forecast(
        self,
        *,
        forecast_type: str,
        farm_id: str,
        horizon_days: int = 30,
        baseline: float = 1.0,
    ) -> dict[str, Any]:
        if forecast_type not in FORECAST_TYPES:
            raise ValidationError(f"forecast_type must be one of {FORECAST_TYPES}")
        factors = {
            "yield": 1.02,
            "weather_impact": 0.95,
            "disease": 1.08,
            "market": 1.03,
            "resource_demand": 1.05,
            "financial": 1.01,
            "supply_chain": 0.98,
        }
        value = round(float(baseline) * factors[forecast_type] * (1 + horizon_days * 0.001), 3)
        fid = _id("aa_fc")
        return self.store.aa_forecasts.save(
            fid,
            {
                "forecast_id": fid,
                "forecast_type": forecast_type,
                "farm_id": farm_id,
                "horizon_days": int(horizon_days),
                "baseline": float(baseline),
                "predicted": value,
                "confidence": 0.74,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"forecasts": self.store.aa_forecasts.count()}


class EnterpriseOptimization:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store

    def optimize(
        self,
        *,
        opt_type: str,
        farm_id: str,
        current_cost: float = 100.0,
        utilization: float = 0.7,
    ) -> dict[str, Any]:
        if opt_type not in OPT_TYPES:
            raise ValidationError(f"opt_type must be one of {OPT_TYPES}")
        saving_pct = {
            "resource": 0.08,
            "equipment": 0.12,
            "labor": 0.07,
            "fuel": 0.1,
            "inventory": 0.09,
            "water": 0.15,
            "energy": 0.11,
        }[opt_type]
        oid = _id("aa_opt")
        return self.store.aa_optimizations.save(
            oid,
            {
                "optimization_id": oid,
                "opt_type": opt_type,
                "farm_id": farm_id,
                "current_cost": float(current_cost),
                "utilization": float(utilization),
                "projected_saving_pct": saving_pct,
                "projected_cost": round(float(current_cost) * (1 - saving_pct), 2),
                "actions": [f"rebalance_{opt_type}", "monitor_kpi"],
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"optimizations": self.store.aa_optimizations.count()}


class AIExecutiveAssistant:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store

    def chat(self, *, message: str, executive_id: str = "ceo") -> dict[str, Any]:
        if not message:
            raise ValidationError("message required")
        cid = _id("aa_echat")
        return self.store.aa_exec_chats.save(
            cid,
            {
                "chat_id": cid,
                "executive_id": executive_id,
                "message": message,
                "reply": "Briefing prepared: prioritize harvest logistics and hedge open wheat exposure.",
                "at": _now(),
            },
        )

    def daily_briefing(self, *, farm_id: str = "", executive_id: str = "ceo") -> dict[str, Any]:
        bid = _id("aa_brief")
        health = self.business_health(farm_id=farm_id or "enterprise")
        return self.store.aa_briefings.save(
            bid,
            {
                "briefing_id": bid,
                "executive_id": executive_id,
                "farm_id": farm_id,
                "highlights": [
                    "Yield outlook stable",
                    "Irrigation demand rising in north fields",
                    "Market bid supportive for wheat",
                ],
                "kpis": health["kpis"],
                "business_health_score": health["score"],
                "at": _now(),
            },
        )

    def business_health(self, *, farm_id: str) -> dict[str, Any]:
        plans = self.store.aa_plans.count()
        forecasts = self.store.aa_forecasts.count()
        opts = self.store.aa_optimizations.count()
        decisions = self.store.aa_decisions.count()
        score = round(min(100.0, 55 + plans * 2 + forecasts * 1.5 + opts * 2 + decisions * 1.2), 1)
        return {
            "farm_id": farm_id,
            "score": score,
            "kpis": {
                "plans": plans,
                "forecasts": forecasts,
                "optimizations": opts,
                "decisions": decisions,
            },
        }

    def investment_recommendation(self, *, theme: str, amount: float) -> dict[str, Any]:
        if not theme:
            raise ValidationError("theme required")
        iid = _id("aa_inv")
        return self.store.aa_investments.save(
            iid,
            {
                "investment_id": iid,
                "theme": theme,
                "amount": float(amount),
                "recommendation": "proceed" if amount < 500000 else "stage_gate",
                "strategic": True,
                "at": _now(),
            },
        )

    def strategic(self, *, farm_id: str) -> dict[str, Any]:
        rid = _id("aa_strat")
        return self.store.aa_strategies.save(
            rid,
            {
                "strategy_id": rid,
                "farm_id": farm_id,
                "recommendations": [
                    "Expand variable-rate nutrition",
                    "Digitize harvest dispatch",
                    "Lock forward sales on 40% of wheat",
                ],
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "chats": self.store.aa_exec_chats.count(),
            "briefings": self.store.aa_briefings.count(),
            "strategies": self.store.aa_strategies.count(),
        }
