"""AI Port Director facade — Sprint 15.7."""

from __future__ import annotations

from typing import Any

from applications.port_enterprise.ai_port_director.director import AIPortDirector, DecisionSupport
from applications.port_enterprise.ai_port_director.services import (
    AutonomousOperations,
    DirectorDashboard,
    DirectorKnowledge,
    ExecutiveAI,
    OperationalIntelligence,
    PredictiveLogistics,
)
from applications.port_enterprise.config import DEFAULT_CONFIG
from applications.port_enterprise.shared.store import PortEnterpriseStore, port_enterprise_store


class AIPortDirectorSuite:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store
        self.director = AIPortDirector(self.store)
        self.decisions = DecisionSupport(self.store)
        self.predictive = PredictiveLogistics(self.store)
        self.autonomous = AutonomousOperations(self.store)
        self.intelligence = OperationalIntelligence(self.store)
        self.executive = ExecutiveAI(self.store)
        self.dashboard = DirectorDashboard(self.store)
        self.knowledge = DirectorKnowledge(self.store)

    def bootstrap(self) -> dict[str, Any]:
        ask = self.director.ask(prompt="What is terminal congestion outlook?", context="terminal")
        self.director.natural_language(utterance="Schedule berth for MV Horizon", intent="schedule")
        adv = self.director.advise(
            advisory_type="port",
            subject="Odessa",
            recommendation="Increase STS crane allocation for evening peak",
        )
        self.director.advise(advisory_type="terminal", subject="CT1", recommendation="Pre-stage reefer plugs")
        self.director.advise(advisory_type="cargo", subject="Reefer lot A", recommendation="Prioritize gate-out")
        self.director.advise(advisory_type="fleet", subject="MV Horizon", recommendation="Confirm pilot window")
        self.director.advise(advisory_type="logistics", subject="Rail corridor", recommendation="Hold spare wagons")
        self.director.advise(advisory_type="executive", subject="Board", recommendation="Approve yard expansion")

        decision = self.decisions.decide(topic="Berth priority", options=["Horizon", "bulk vessel", "defer"])
        scenario = self.decisions.scenario(name="Storm delay", assumptions={"wind_kt": 35})
        self.decisions.recommend(domain="yard", action="reblock high movers")
        self.decisions.allocate_resources(resource="STS crane", quantity=2, target="CT1")
        self.decisions.set_priority(item_ref="MV Horizon", priority="high")
        cost = self.decisions.optimize_cost(scope="terminal ops", baseline=100000)
        self.decisions.profitability(segment="containers", revenue=500000, cost=320000)
        self.decisions.strategic_plan(horizon="2027", goals=["automation", "green corridor"])

        arrival = self.predictive.predict_arrival(vessel_ref="MV Horizon", eta_hours=18)
        self.predictive.predict_departure(vessel_ref="MV Horizon", etd_hours=42)
        self.predictive.cargo_flow(terminal_ref="CT1", teu=4200, days=7)
        self.predictive.congestion(terminal_ref="CT1")
        self.predictive.equipment_utilization(equipment_type="sts", utilization_pct=78)
        demand = self.predictive.demand(corridor="Odessa-Istanbul", baseline=1200, days=30)
        self.predictive.supply_chain(chain_ref="Sea-Rail-Truck")
        self.predictive.weather_impact(location="Odessa", severity=0.35)

        dock = self.autonomous.schedule_dock(
            dock_ref="Dock A", vessel_ref="MV Horizon", window_start="2026-08-21T08:00:00Z"
        )
        berth = self.autonomous.allocate_berth(berth_ref="Berth A1", vessel_ref="MV Horizon")
        self.autonomous.schedule_equipment(equipment_ref="STS-1", task="discharge")
        self.autonomous.plan_container_move(container_ref="MSCU1", from_slot="A1", to_slot="B2")
        yard = self.autonomous.optimize_yard(yard_ref="Yard North")
        self.autonomous.coordinate_fleet(fleet_ref="Port Fleet", objective="throughput")
        self.autonomous.schedule_maintenance(asset_ref="STS-1", due_at="2026-09-01")
        self.autonomous.emergency_plan(incident_type="oil_spill", severity="high")

        risk = self.intelligence.risk_assess(domain="operations", score=0.32)
        self.intelligence.delay_predict(subject_ref="MV Horizon", risk=0.22)
        self.intelligence.bottleneck(location="Gate G1", severity=0.4)
        self.intelligence.incident_predict(domain="yard", probability=0.15)
        self.intelligence.capacity_forecast(node="CT1", teu=12000)
        self.intelligence.kpi_predict(kpi="otif", baseline=94.0)
        self.intelligence.optimize_performance(scope="terminal")

        chat = self.executive.chat(message="Summarize port health", executive="CEO")
        briefing = self.executive.daily_briefing(date="2026-08-20")
        health = self.executive.health_score(score=88.5)
        self.executive.strategic_recommendation(theme="capacity", action="Expand cold storage")
        self.executive.financial_insight(metric="ebitda", value=12.4)
        invest = self.executive.investment_plan(project="AGV fleet", amount=4_500_000)

        for rtype, key in (
            ("director", ask["assistant_id"]),
            ("decision", decision["decision_id"]),
            ("forecast", arrival["prediction_id"]),
            ("operations", yard["optimization_id"]),
            ("executive", briefing["briefing_id"]),
        ):
            self.knowledge.publish(registry_type=rtype, key=key, payload={"bootstrap": True})

        dash = self.dashboard.render(dashboard_type="ai_director")
        return {
            "bootstrap": True,
            "assistant_id": ask["assistant_id"],
            "advisory_id": adv["advisory_id"],
            "decision_id": decision["decision_id"],
            "scenario_id": scenario["scenario_id"],
            "cost_id": cost["optimization_id"],
            "arrival_id": arrival["prediction_id"],
            "demand_id": demand["forecast_id"],
            "dock_id": dock["schedule_id"],
            "berth_id": berth["allocation_id"],
            "yard_id": yard["optimization_id"],
            "risk_id": risk["assessment_id"],
            "chat_id": chat["chat_id"],
            "briefing_id": briefing["briefing_id"],
            "health_id": health["score_id"],
            "investment_id": invest["plan_id"],
            "dashboard_id": dash["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "director": self.director.status(),
            "decisions": self.decisions.status(),
            "predictive": self.predictive.status(),
            "autonomous": self.autonomous.status(),
            "intelligence": self.intelligence.status(),
            "executive": self.executive.status(),
            "dashboard": self.dashboard.status(),
            "knowledge": self.knowledge.status(),
        }


ai_port_director = AIPortDirectorSuite()
