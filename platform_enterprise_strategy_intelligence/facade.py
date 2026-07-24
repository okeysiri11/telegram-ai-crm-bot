"""Strategy Intelligence library facade — Sprint 24.7."""

from __future__ import annotations

from typing import Any

from platform_enterprise_strategy_intelligence.council import AIStrategicCouncil
from platform_enterprise_strategy_intelligence.dashboard import StrategyDashboard
from platform_enterprise_strategy_intelligence.expansion import ExpansionPlanner
from platform_enterprise_strategy_intelligence.forecast import LongTermForecast
from platform_enterprise_strategy_intelligence.goals import StrategicGoalsEngine
from platform_enterprise_strategy_intelligence.integrations import StrategyIntegrations
from platform_enterprise_strategy_intelligence.investment import InvestmentAnalyzer
from platform_enterprise_strategy_intelligence.models import PRINCIPLES
from platform_enterprise_strategy_intelligence.owner import OwnerStrategyDecision
from platform_enterprise_strategy_intelligence.registry import StrategyRegistry
from platform_enterprise_strategy_intelligence.risk import StrategicRiskEngine
from platform_enterprise_strategy_intelligence.scenarios import StrategicScenarioBuilder


class StrategyIntelligenceLibrary:
    def __init__(self) -> None:
        self.registry = StrategyRegistry()
        self.goals = StrategicGoalsEngine()
        self.forecast = LongTermForecast()
        self.council = AIStrategicCouncil()
        self.scenarios = StrategicScenarioBuilder()
        self.investment = InvestmentAnalyzer()
        self.expansion = ExpansionPlanner()
        self.risk = StrategicRiskEngine()
        self.dashboard = StrategyDashboard()
        self.owner = OwnerStrategyDecision()
        self.integrations = StrategyIntegrations()

    def principles(self) -> list[str]:
        return list(PRINCIPLES)

    def bootstrap(self) -> dict[str, Any]:
        self.__init__()
        goal = self.goals.define(goal_type="revenue_growth", target_value=25.0)
        strategy = self.registry.create(
            strategy_id="str_scale_2027",
            name="Scale revenue across branches",
            goal=goal["goal_type"],
            horizon="three_years",
            kpis={"revenue_growth_pct": 25.0, "branches": 3},
        )
        forecast = self.forecast.project(baseline=1_000_000, growth_rate=0.12, horizon="three_years")
        scenarios = self.scenarios.build(baseline_value=forecast["projected"], strategy_id=strategy["strategy_id"])
        investment = self.investment.analyze(
            investment=250_000,
            annual_return=90_000,
            cashflow_delta=-40_000,
            profit_delta=80_000,
            staff_impact=5,
            customer_impact=0.15,
        )
        expansion = self.expansion.plan(
            items=[
                {"dimension": "branches", "name": "North Branch"},
                {"dimension": "products", "name": "Premium Package"},
            ]
        )
        risk = self.risk.assess(scores={"market": 0.4, "financial": 0.35, "workforce": 0.3, "technology": 0.25, "operational": 0.3})
        review = self.council.review(strategy=strategy, risk_score=risk["overall_risk"])
        strategy = self.registry.set_status(strategy, status="awaiting_owner")
        decision = self.owner.decide(action="approve", actor="platform_owner", strategy_id=strategy["strategy_id"])
        dash = self.dashboard.render(
            strategy=strategy,
            deviations=[],
            kpi_forecast={"probability": 0.72, "horizon": "three_years"},
            ai_recommendations=["approve_with_conservative_buffer"],
            alternatives=scenarios["scenarios"],
        )
        links = self.integrations.link()
        return {
            "bootstrap": True,
            "principles": self.principles(),
            "strategy_intelligence_ready": True,
            "strategic_goals_ready": True,
            "long_term_forecast_ready": True,
            "owner_strategy_ready": True,
            "ai_may_act": False,
            "autonomous_decide": False,
            "council_reviewed": review["unified"],
            "measurable_goals": goal["measurable"],
            "duplicates_core_logic": False,
            "status": "ready",
            "integrations": links,
            "full": {
                "goal": goal,
                "strategy": strategy,
                "forecast": forecast,
                "scenarios": scenarios,
                "investment": investment,
                "expansion": expansion,
                "risk": risk,
                "council": review,
                "decision": decision,
                "dashboard": dash,
                "links": links,
            },
        }

    def status(self) -> dict[str, Any]:
        return {
            "components": [
                "registry",
                "goals",
                "forecast",
                "council",
                "scenarios",
                "investment",
                "expansion",
                "risk",
                "dashboard",
                "owner",
            ],
            "principles": self.principles(),
            "pipeline": [
                "strategy_intelligence",
                "multi_agent_council",
                "owner_approval",
                "execution_workflow",
            ],
        }


strategy_intelligence_library = StrategyIntelligenceLibrary()
