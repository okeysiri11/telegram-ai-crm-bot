"""AI Agronomist Suite facade — Sprint 14.7."""

from __future__ import annotations

from typing import Any

from applications.agro_enterprise.ai_agronomist.agronomist import AIAgronomistAssistant, DecisionSupport
from applications.agro_enterprise.ai_agronomist.planning import (
    AIExecutiveAssistant,
    AutonomousPlanning,
    EnterpriseOptimization,
    PredictiveIntelligence,
)
from applications.agro_enterprise.ai_agronomist.services import AIAgronomistDashboard, AIAgronomistKnowledge
from applications.agro_enterprise.config import DEFAULT_CONFIG
from applications.agro_enterprise.shared.store import AgroEnterpriseStore, agro_enterprise_store


class AIAgronomistSuite:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store
        self.agronomist = AIAgronomistAssistant(self.store)
        self.decisions = DecisionSupport(self.store)
        self.planning = AutonomousPlanning(self.store)
        self.forecasts = PredictiveIntelligence(self.store)
        self.optimization = EnterpriseOptimization(self.store)
        self.executive = AIExecutiveAssistant(self.store)
        self.dashboard = AIAgronomistDashboard(self.store)
        self.knowledge = AIAgronomistKnowledge(self.store)

    def bootstrap(self) -> dict[str, Any]:
        farm_id = "farm_ai_bootstrap"
        consult = self.agronomist.consult(
            query="What disease advisory for wheat under high humidity?",
            farm_id=farm_id,
        )
        for atype in ("crop", "soil", "disease", "pest", "nutrition", "harvest", "season"):
            self.agronomist.advise(advisory_type=atype, farm_id=farm_id)

        decision = self.decisions.decide(
            intent="profit",
            farm_id=farm_id,
            options=["hold_inventory", "sell_forward"],
            risk_score=0.35,
            cost=10000,
            profit=18000,
        )
        scenario = self.decisions.scenario(
            farm_id=farm_id,
            name="Dry July",
            assumptions={"yield_delta_pct": -8, "cost_delta_pct": 5},
        )
        rec = self.decisions.recommend(farm_id=farm_id, focus="executive")
        self.decisions.prioritize(
            farm_id=farm_id,
            tasks=["irrigation_north", "scouting", "harvest_prep", "fertilizer_topdress"],
        )

        plans = []
        for ptype, title in (
            ("season", "2026 Season Plan"),
            ("field_work", "Week 30 Fieldwork"),
            ("machinery", "Combine Rotation"),
            ("drone", "NDVI Survey Grid"),
            ("irrigation", "North Pivot Schedule"),
            ("fertilization", "VRA Nitrogen Pass"),
            ("harvest", "Wheat Window"),
            ("workforce", "Harvest Crew Roster"),
        ):
            plans.append(
                self.planning.create_plan(
                    plan_type=ptype,
                    farm_id=farm_id,
                    title=title,
                    window_start="2026-07-01",
                    window_end="2026-07-20",
                )
            )
        self.planning.activate(plans[0]["plan_id"])

        forecasts = []
        for ftype in (
            "yield",
            "weather_impact",
            "disease",
            "market",
            "resource_demand",
            "financial",
            "supply_chain",
        ):
            forecasts.append(
                self.forecasts.forecast(forecast_type=ftype, farm_id=farm_id, horizon_days=30, baseline=100)
            )

        opts = []
        for otype in ("resource", "equipment", "labor", "fuel", "inventory", "water", "energy"):
            opts.append(self.optimization.optimize(opt_type=otype, farm_id=farm_id, current_cost=50000))

        chat = self.executive.chat(message="What should we prioritize this week?", executive_id="ceo")
        briefing = self.executive.daily_briefing(farm_id=farm_id)
        strategy = self.executive.strategic(farm_id=farm_id)
        inv = self.executive.investment_recommendation(theme="precision_irrigation", amount=320000)

        for rtype, key in (
            ("agronomist", consult["consultation_id"]),
            ("decision", decision["decision_id"]),
            ("planning", plans[0]["plan_id"]),
            ("forecast", forecasts[0]["forecast_id"]),
            ("optimization", opts[0]["optimization_id"]),
        ):
            self.knowledge.publish(registry_type=rtype, key=key, payload={"bootstrap": True})

        dash = self.dashboard.render(dashboard_type="executive_intelligence")
        return {
            "bootstrap": True,
            "consultation_id": consult["consultation_id"],
            "decision_id": decision["decision_id"],
            "scenario_id": scenario["scenario_id"],
            "recommendation_id": rec["recommendation_id"],
            "plan_id": plans[0]["plan_id"],
            "forecast_id": forecasts[0]["forecast_id"],
            "optimization_id": opts[0]["optimization_id"],
            "chat_id": chat["chat_id"],
            "briefing_id": briefing["briefing_id"],
            "strategy_id": strategy["strategy_id"],
            "investment_id": inv["investment_id"],
            "business_health_score": briefing["business_health_score"],
            "dashboard_id": dash["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "agronomist": self.agronomist.status(),
            "decisions": self.decisions.status(),
            "planning": self.planning.status(),
            "forecasts": self.forecasts.status(),
            "optimization": self.optimization.status(),
            "executive": self.executive.status(),
            "dashboard": self.dashboard.status(),
            "knowledge": self.knowledge.status(),
        }


ai_agronomist = AIAgronomistSuite()
