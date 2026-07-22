# Executive Dashboard — fleet KPIs, costs, live map, AI assistant.

from __future__ import annotations

from applications.auto_marketplace.ai_operations.engine import AIOperationsEngine, ai_operations_engine
from applications.auto_marketplace.fleet.engine import FleetEngine, fleet_engine
from applications.auto_marketplace.telematics.engine import TelematicsEngine, telematics_engine


class ExecutiveDashboardEngine:
    def __init__(
        self,
        fleet: FleetEngine | None = None,
        telematics: TelematicsEngine | None = None,
        ai: AIOperationsEngine | None = None,
    ) -> None:
        self._fleet = fleet or fleet_engine
        self._telematics = telematics or telematics_engine
        self._ai = ai or ai_operations_engine

    def kpis(self, fleet_id: str = "") -> dict:
        analytics = self._fleet.analytics(fleet_id)
        util = self._ai.utilization_prediction(fleet_id)
        return {
            "fleet_id": fleet_id,
            "vehicles": analytics["vehicles"],
            "utilization_pct": analytics["utilization_pct"],
            "predicted_utilization_pct": util["predicted_utilization_pct"],
            "revenue": analytics["revenue"],
            "operating_costs": analytics["total_cost"],
            "maintenance_costs": round(
                sum(v.costs.get("maintenance", 0) for v in self._fleet.list_vehicles(fleet_id=fleet_id)), 2
            ),
            "profitability": analytics["profitability"],
        }

    def live_map(self, fleet_id: str = "") -> list[dict]:
        return self._telematics.live_map(fleet_id)

    def assistant(self, question: str, fleet_id: str = "") -> dict:
        kpis = self.kpis(fleet_id)
        q = (question or "").lower()
        if "cost" in q:
            answer = f"Operating costs are {kpis['operating_costs']} with maintenance {kpis['maintenance_costs']}."
        elif "util" in q:
            answer = f"Current utilization {kpis['utilization_pct']}%, predicted {kpis['predicted_utilization_pct']}%."
        elif "profit" in q or "revenue" in q:
            answer = f"Revenue {kpis['revenue']}, profitability {kpis['profitability']}."
        else:
            answer = (
                f"Fleet has {kpis['vehicles']} vehicles, utilization {kpis['utilization_pct']}%, "
                f"profitability {kpis['profitability']}."
            )
        return {"question": question, "answer": answer, "kpis": kpis}

    def metrics(self) -> dict:
        return {"executive_kpis": self.kpis()}


executive_dashboard_engine = ExecutiveDashboardEngine()
