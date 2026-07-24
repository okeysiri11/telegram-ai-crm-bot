"""Simulation Engine Suite facade — Sprint 20.9."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store
from applications.enterprise_hub.simulation_engine.analytics.confidence import ConfidenceAnalytics
from applications.enterprise_hub.simulation_engine.analytics.executive import ExecutiveReporting
from applications.enterprise_hub.simulation_engine.analytics.predictions import PredictionAnalytics
from applications.enterprise_hub.simulation_engine.analytics.recommendations import RecommendationAnalytics
from applications.enterprise_hub.simulation_engine.decision_engine import DecisionEngine
from applications.enterprise_hub.simulation_engine.forecasting_engine import ForecastingEngine
from applications.enterprise_hub.simulation_engine.integrations import SimulationIntegrations
from applications.enterprise_hub.simulation_engine.monte_carlo import MonteCarloSimulation
from applications.enterprise_hub.simulation_engine.optimization.engine import OptimizationEngine
from applications.enterprise_hub.simulation_engine.recommendation_engine import RecommendationEngine
from applications.enterprise_hub.simulation_engine.risk_engine import RiskEngine
from applications.enterprise_hub.simulation_engine.scenario_engine import ScenarioEngine
from applications.enterprise_hub.simulation_engine.scenarios.construction import ConstructionScenario
from applications.enterprise_hub.simulation_engine.scenarios.custom import CustomScenario
from applications.enterprise_hub.simulation_engine.scenarios.finance import FinanceScenario
from applications.enterprise_hub.simulation_engine.scenarios.hr import HrScenario
from applications.enterprise_hub.simulation_engine.scenarios.logistics import LogisticsScenario
from applications.enterprise_hub.simulation_engine.scenarios.manufacturing import ManufacturingScenario
from applications.enterprise_hub.simulation_engine.scenarios.maritime import MaritimeScenario
from applications.enterprise_hub.simulation_engine.scenarios.procurement import ProcurementScenario
from applications.enterprise_hub.simulation_engine.scenarios.warehouse import WarehouseScenario
from applications.enterprise_hub.simulation_engine.sensitivity_analysis import SensitivityAnalysis
from applications.enterprise_hub.simulation_engine.simulation_history import SimulationHistory
from applications.enterprise_hub.simulation_engine.simulation_manager import SimulationManager
from applications.enterprise_hub.simulation_engine.simulation_registry import SimulationRegistry
from applications.enterprise_hub.simulation_engine.simulation_scheduler import SimulationScheduler


class SimulationEngineSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.manager = SimulationManager(self.store)
        self.registry = SimulationRegistry(self.store)
        self.scenarios = ScenarioEngine(self.store)
        self.decisions = DecisionEngine(self.store)
        self.forecasts = ForecastingEngine(self.store)
        self.optimization = OptimizationEngine(self.store)
        self.risks = RiskEngine(self.store)
        self.monte_carlo = MonteCarloSimulation(self.store)
        self.sensitivity = SensitivityAnalysis(self.store)
        self.scheduler = SimulationScheduler(self.store)
        self.history = SimulationHistory(self.store)
        self.recommendation_engine = RecommendationEngine(self.store)
        self.integrations = SimulationIntegrations(self.store)
        self.predictions = PredictionAnalytics(self.store)
        self.confidence = ConfidenceAnalytics(self.store)
        self.recommendation_analytics = RecommendationAnalytics(self.store)
        self.executive = ExecutiveReporting(self.store)
        # alias for analytics API compatibility
        self.recommendations = self.recommendation_analytics
        self.finance = FinanceScenario(self.store)
        self.logistics = LogisticsScenario(self.store)
        self.manufacturing = ManufacturingScenario(self.store)
        self.warehouse = WarehouseScenario(self.store)
        self.hr = HrScenario(self.store)
        self.procurement = ProcurementScenario(self.store)
        self.construction = ConstructionScenario(self.store)
        self.maritime = MaritimeScenario(self.store)
        self.custom = CustomScenario(self.store)

    def dashboard(self) -> dict[str, Any]:
        """Decision Analytics Dashboard."""
        pred = self.predictions.report()
        conf = self.confidence.report()
        rec_an = self.recommendation_analytics.report()
        exec_rep = self.executive.report()
        active = [s for s in self.store.esi_scenarios.list_all() if s.get("status") in ("draft", "completed")]
        decisions = self.store.esi_decisions.list_all()
        forecasts = self.store.esi_forecasts.list_all()
        risks = self.store.esi_risks.list_all()
        ai_recs = self.store.esi_recommendations.list_all()
        success_probs = []
        for d in decisions:
            ranked = d.get("ranked") or []
            if ranked:
                success_probs.append(float((ranked[0].get("scores") or {}).get("success_probability", 0)))
        avg_success = (sum(success_probs) / len(success_probs)) if success_probs else 0
        decision_history = [
            {
                "decision_id": d.get("decision_id"),
                "best_option": d.get("best_option"),
                "context": d.get("context"),
                "at": d.get("at"),
            }
            for d in decisions
        ]
        return {
            "active_scenarios": [
                {"scenario_id": s["scenario_id"], "domain": s.get("domain"), "kind": s.get("kind"), "question": s.get("question")}
                for s in active
            ],
            "active_scenario_count": len(active),
            "forecasts": [{"forecast_id": f["forecast_id"], "target": f.get("target"), "final": f.get("final")} for f in forecasts],
            "success_probability": round(avg_success, 2),
            "potential_profit": exec_rep.get("potential_profit_index"),
            "potential_loss": exec_rep.get("potential_loss_index"),
            "risk_level": exec_rep.get("risk_level") if exec_rep.get("risk_level") is not None else self.risks.status()["avg_overall"],
            "ai_recommendations": [
                {"recommendation_id": r["recommendation_id"], "top_action": r.get("top_action"), "actions": r.get("actions")}
                for r in ai_recs
            ],
            "decision_history": decision_history,
            "scenarios": self.scenarios.status()["scenarios"],
            "decisions": self.decisions.status()["decisions"],
            "optimizations": self.optimization.status()["optimizations"],
            "monte_carlo_runs": self.monte_carlo.status()["monte_carlo_runs"],
            "confidence": conf.get("confidence"),
            "recommendation_count": rec_an.get("count"),
            "prediction_id": pred["analytics_id"],
            "confidence_id": conf["analytics_id"],
            "recommendations_id": rec_an["analytics_id"],
            "executive_id": exec_rep["analytics_id"],
            "risk_assessments": len(risks),
        }

    def bootstrap(self) -> dict[str, Any]:
        links = self.integrations.bootstrap_links()
        s1 = self.finance.build(
            question="What happens to profit if fuel cost rises 20%?",
            kind="resource_cost_change",
            parameters={"cost_pct": 20, "fuel_cost": 1.2},
        )
        s2 = self.logistics.build(
            question="What if demand increases 15%?",
            kind="demand_increase",
            parameters={"demand_pct": 15},
        )
        s3 = self.manufacturing.build(
            question="What if Line-1 fails?",
            kind="equipment_failure",
            parameters={"shock_pct": 30},
        )
        s4 = self.maritime.build(
            question="What if berth delay grows 2 days?",
            kind="what_if",
            parameters={"shock_pct": 12},
        )
        self.registry.register(name="fuel-shock", kind="scenario", ref_id=s1["scenario_id"])
        self.registry.register(name="line-failure", kind="scenario", ref_id=s3["scenario_id"])

        r1 = self.scenarios.run(scenario_id=s1["scenario_id"])
        sched = self.scheduler.schedule(scenario_id=s2["scenario_id"], mode="manual", run_at="immediate", priority=1)
        executed = self.scheduler.execute(schedule_id=sched["schedule_id"])

        evt_sched = self.scheduler.schedule(
            scenario_id=s4["scenario_id"], mode="event_bus", event_type="ShipmentDelayed", priority=2
        )
        evt_runs = self.scheduler.on_event(event_type="ShipmentDelayed", payload={"hours": 6})
        cont = self.scheduler.schedule(
            scenario_id=s3["scenario_id"], mode="continuous", interval_sec=60, priority=3
        )
        cont_ticks = self.scheduler.tick_continuous()

        decision = self.decisions.evaluate(
            context="capacity expansion",
            options=[
                {"option_id": "expand", "label": "Expand plant", "profit": 80, "cost": 70, "risk": 40, "time": 60, "efficiency": 75, "success_probability": 70},
                {"option_id": "outsource", "label": "Outsource", "profit": 55, "cost": 40, "risk": 55, "time": 30, "efficiency": 60, "success_probability": 65},
                {"option_id": "defer", "label": "Defer", "profit": 30, "cost": 10, "risk": 20, "time": 10, "efficiency": 40, "success_probability": 90},
            ],
            weights={"profit": 1.5, "risk": 1.2, "cost": 1.0},
        )

        fc_sales = self.forecasts.forecast(target="sales", baseline=1000, growth_pct=4)
        fc_cash = self.forecasts.forecast(target="cash_flow", baseline=500, growth_pct=3)
        fc_maint = self.forecasts.forecast(target="maintenance", baseline=50, growth_pct=2)

        opt_batch = self.optimization.optimize_all(context={"baseline": 200})
        risk = self.risks.assess(
            scenario_id=s3["scenario_id"],
            exposures={"financial": 0.35, "operational": 0.7, "manufacturing": 0.65, "logistics": 0.4},
        )
        mc = self.monte_carlo.run(scenario_id=s1["scenario_id"], iterations=200, mean=100, stdev=12, seed=7)
        sens = self.sensitivity.analyze(
            parameters={"fuel_cost": 1.0, "demand": 1.0, "wage_rate": 1.0},
            outcome_key="profit",
        )
        ai_rec = self.recommendation_engine.generate(
            scenario_id=s3["scenario_id"],
            decision_id=decision["decision_id"],
            risk_id=risk["risk_id"],
        )

        self.history.record(kind="scenario", ref_id=s1["scenario_id"], summary={"run_id": r1["run_id"]})
        self.history.record(kind="decision", ref_id=decision["decision_id"], summary={"best": decision["best_option"]})
        self.history.record(kind="monte_carlo", ref_id=mc["simulation_id"], summary={"p50": mc["p50"]})
        self.history.record(kind="recommendation", ref_id=ai_rec["recommendation_id"], summary={"top": ai_rec["top_action"]})

        dash = self.dashboard()
        return {
            "bootstrap": True,
            "scenario_ids": [s1["scenario_id"], s2["scenario_id"], s3["scenario_id"], s4["scenario_id"]],
            "run_id": r1["run_id"],
            "schedule_id": sched["schedule_id"],
            "schedule_completed": executed["status"] == "completed",
            "event_schedule_id": evt_sched["schedule_id"],
            "event_triggered": len(evt_runs) >= 1,
            "continuous_schedule_id": cont["schedule_id"],
            "continuous_ticks": len(cont_ticks),
            "decision_id": decision["decision_id"],
            "best_option": decision["best_option"],
            "forecast_ids": [fc_sales["forecast_id"], fc_cash["forecast_id"], fc_maint["forecast_id"]],
            "opt_batch_id": opt_batch["batch_id"],
            "risk_id": risk["risk_id"],
            "critical_risks": risk["critical"],
            "monte_carlo_id": mc["simulation_id"],
            "sensitivity_id": sens["analysis_id"],
            "top_driver": sens["top_driver"],
            "recommendation_id": ai_rec["recommendation_id"],
            "top_recommendation": ai_rec["top_action"],
            "integrations_linked": links["linked"],
            "integration_targets": links["targets"],
            "dashboard": dash,
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        base = self.manager.status()
        base["recommendation_engine"] = self.recommendation_engine.status()
        base["integrations"] = self.integrations.status()
        base["registry"] = self.registry.status()
        return base


simulation_engine = SimulationEngineSuite()
