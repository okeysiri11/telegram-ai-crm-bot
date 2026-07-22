# Executive AI Engine + Decision Support Engine.

from __future__ import annotations

import uuid

from events.publisher import publish

from applications.port_erp.alerts.engine import AlertsEngine, alerts_engine
from applications.port_erp.dashboard.engine import ExecutiveDashboardEngine, executive_dashboard_engine
from applications.port_erp.digital_twin.events import ExecutiveBriefingReadyEvent
from applications.port_erp.digital_twin.models import (
    AlertSeverity,
    AlertType,
    DecisionRecommendation,
)
from applications.port_erp.optimization.engine import OptimizationEngine, optimization_engine
from applications.port_erp.prediction.engine import PredictiveAnalyticsEngine, predictive_analytics_engine
from applications.port_erp.shared.store import PortStore, port_store
from applications.port_erp.simulation.engine import SimulationEngine, simulation_engine


class DecisionSupportEngine:
    def __init__(
        self,
        store: PortStore | None = None,
        dashboard: ExecutiveDashboardEngine | None = None,
        prediction: PredictiveAnalyticsEngine | None = None,
    ) -> None:
        self._store = store or port_store
        self._dashboard = dashboard or executive_dashboard_engine
        self._prediction = prediction or predictive_analytics_engine

    def recommend(self) -> list[DecisionRecommendation]:
        recs: list[DecisionRecommendation] = []
        for bottleneck in self._dashboard.bottlenecks():
            if bottleneck["type"] == "congestion":
                recs.append(
                    DecisionRecommendation(
                        title="Relieve berth congestion",
                        rationale=f"Congestion index {bottleneck['value']}",
                        priority="high" if bottleneck.get("severity") == "critical" else "medium",
                        actions=["replan berths", "accelerate departures"],
                    )
                )
            if bottleneck["type"] == "equipment":
                recs.append(
                    DecisionRecommendation(
                        title="Restore equipment availability",
                        rationale="Available equipment below 30%",
                        priority="high",
                        actions=["exit maintenance early", "rent temporary RTG"],
                    )
                )
        dwell = self._prediction.predict_dwell_time()
        if dwell.value > 48:
            recs.append(
                DecisionRecommendation(
                    title="Reduce container dwell",
                    rationale=f"Predicted dwell {dwell.value}h",
                    priority="medium",
                    actions=["prioritize gate-out", "yard compaction"],
                )
            )
        if not recs:
            recs.append(
                DecisionRecommendation(
                    title="Maintain steady operations",
                    rationale="No critical bottlenecks detected",
                    priority="low",
                    actions=["continue monitoring"],
                )
            )
        for rec in recs:
            self._store.decision_recommendations.save(rec.recommendation_id, rec)
        return recs


class ExecutiveAIEngine:
    def __init__(
        self,
        store: PortStore | None = None,
        dashboard: ExecutiveDashboardEngine | None = None,
        decisions: DecisionSupportEngine | None = None,
        optimization: OptimizationEngine | None = None,
        simulation: SimulationEngine | None = None,
        alerts: AlertsEngine | None = None,
        prediction: PredictiveAnalyticsEngine | None = None,
    ) -> None:
        self._store = store or port_store
        self.dashboard = dashboard or executive_dashboard_engine
        self.decisions = decisions or DecisionSupportEngine(
            store=self._store, dashboard=self.dashboard, prediction=prediction
        )
        self.optimization = optimization or optimization_engine
        self.simulation = simulation or simulation_engine
        self.alerts = alerts or alerts_engine
        self.prediction = prediction or predictive_analytics_engine

    async def briefing(self) -> dict:
        kpis = self.dashboard.kpis()
        recommendations = self.decisions.recommend()
        congestion = self.prediction.predict_congestion()
        if congestion.value >= 0.8:
            await self.alerts.raise_alert(
                alert_type=AlertType.CRITICAL_CONGESTION,
                title="Critical port congestion",
                message=f"Congestion index {congestion.value}",
                severity=AlertSeverity.CRITICAL,
            )
        briefing_id = str(uuid.uuid4())
        payload = {
            "briefing_id": briefing_id,
            "kpis": [k.to_dict() for k in kpis],
            "bottlenecks": self.dashboard.bottlenecks(),
            "recommendations": [r.to_dict() for r in recommendations],
            "alerts": [a.to_dict() for a in self.alerts.list_alerts(acknowledged=False)[:10]],
        }
        await publish(
            ExecutiveBriefingReadyEvent(briefing_id=briefing_id, kpi_count=len(kpis))
        )
        return payload


decision_support_engine = DecisionSupportEngine()
executive_ai_engine = ExecutiveAIEngine(decisions=decision_support_engine)
