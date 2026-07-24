"""Simulation Lab library facade — Sprint 24.4."""

from __future__ import annotations

from typing import Any

from platform_enterprise_simulation_lab.comparator import RecommendationComparator
from platform_enterprise_simulation_lab.debate import AIDebateMode
from platform_enterprise_simulation_lab.engine import SimulationEngine
from platform_enterprise_simulation_lab.history import SimulationHistory
from platform_enterprise_simulation_lab.impact import AIImpactAnalyzer
from platform_enterprise_simulation_lab.integrations import SimulationLabIntegrations
from platform_enterprise_simulation_lab.models import PRINCIPLES
from platform_enterprise_simulation_lab.multi_scenario import MultiScenarioEngine
from platform_enterprise_simulation_lab.owner import OwnerSimulationDecision
from platform_enterprise_simulation_lab.registry import ScenarioRegistry
from platform_enterprise_simulation_lab.resources import ResourceSimulator
from platform_enterprise_simulation_lab.risk_sim import RiskSimulator
from platform_enterprise_simulation_lab.what_if import WhatIfAnalysis


class SimulationLabLibrary:
    def __init__(self) -> None:
        self.registry = ScenarioRegistry()
        self.engine = SimulationEngine()
        self.what_if = WhatIfAnalysis()
        self.multi_scenario = MultiScenarioEngine()
        self.impact = AIImpactAnalyzer()
        self.resources = ResourceSimulator()
        self.risk_sim = RiskSimulator()
        self.comparator = RecommendationComparator()
        self.debate = AIDebateMode()
        self.history = SimulationHistory()
        self.owner = OwnerSimulationDecision()
        self.integrations = SimulationLabIntegrations()

    def principles(self) -> list[str]:
        return list(PRINCIPLES)

    def bootstrap(self) -> dict[str, Any]:
        self.__init__()
        scenario = self.registry.create(
            scenario_id="scn_price_up",
            name="Increase prices 5%",
            description="What-if price increase",
            models=["predictive_intelligence", "commerce_core"],
        )
        what = self.what_if.analyze(question="increase_prices", intensity=1.0)
        sim = self.engine.run_bundle(changes=what["domain_deltas"])
        impacts = self.impact.analyze(deltas=what["domain_deltas"])
        scenarios = self.multi_scenario.expand(baseline=sim["results"][0]["projected"], domain="finance")
        resources = self.resources.calculate(staff_delta=what["domain_deltas"].get("workforce", 0), sales_delta=what["domain_deltas"].get("sales", 0))
        risks = self.risk_sim.assess(impact_risks=impacts["impacts"].get("risks", 0.2))
        compared = self.comparator.compare(
            options=[
                {"option_id": "raise_prices", "pros": ["margin"], "cons": ["churn"], "cost": 0, "risks": 0.3, "expected_profit": 800, "payback_days": 30},
                {"option_id": "keep_prices", "pros": ["stability"], "cons": ["flat_growth"], "cost": 0, "risks": 0.1, "expected_profit": 200, "payback_days": 0},
            ]
        )
        debate = self.debate.debate(scenario_name=scenario["name"], impacts=impacts["impacts"])
        hist = self.history.save(scenario_id=scenario["scenario_id"], results={"impacts": impacts}, decision=None)
        scenario = self.registry.record_run(scenario, run_id="run_boot", result_summary="sandbox_ok")
        owner = self.owner.decide(action="approve", actor="platform_owner", scenario_id=scenario["scenario_id"], notes="pilot only")
        links = self.integrations.link()
        return {
            "bootstrap": True,
            "principles": self.principles(),
            "simulation_lab_ready": True,
            "what_if_ready": True,
            "multi_scenario_ready": True,
            "owner_simulation_ready": True,
            "sandbox": True,
            "mutates_production": False,
            "ai_may_act": False,
            "council_debated": debate["unified_report"],
            "options_compared": len(compared["options"]),
            "duplicates_core_logic": False,
            "status": "ready",
            "integrations": links,
            "full": {
                "scenario": scenario,
                "what_if": what,
                "simulation": sim,
                "impacts": impacts,
                "scenarios": scenarios,
                "resources": resources,
                "risks": risks,
                "comparison": compared,
                "debate": debate,
                "history": hist,
                "owner": owner,
                "links": links,
            },
        }

    def status(self) -> dict[str, Any]:
        return {
            "components": [
                "registry",
                "engine",
                "what_if",
                "multi_scenario",
                "impact",
                "resources",
                "risk_sim",
                "comparator",
                "debate",
                "history",
                "owner",
            ],
            "principles": self.principles(),
            "sandbox": True,
        }


simulation_lab_library = SimulationLabLibrary()
