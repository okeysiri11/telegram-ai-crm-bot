# Executive Dashboard Engine — live KPIs and bottlenecks.

from __future__ import annotations

from applications.port_erp.digital_twin.engine import DigitalTwinEngine, digital_twin_engine
from applications.port_erp.digital_twin.models import ExecutiveKPI
from applications.port_erp.prediction.engine import PredictiveAnalyticsEngine, predictive_analytics_engine
from applications.port_erp.shared.store import PortStore, port_store


class ExecutiveDashboardEngine:
    def __init__(
        self,
        store: PortStore | None = None,
        twin: DigitalTwinEngine | None = None,
        prediction: PredictiveAnalyticsEngine | None = None,
    ) -> None:
        self._store = store or port_store
        self._twin = twin or digital_twin_engine
        self._prediction = prediction or predictive_analytics_engine

    def kpis(self) -> list[ExecutiveKPI]:
        berths = self._store.berths.count() or 1
        occupied = len([b for b in self._store.berths.list_all() if getattr(b, "status", "") == "occupied"])
        slots = self._store.yard_slots.count() or 1
        yard_occ = len(
            [s for s in self._store.yard_slots.list_all() if getattr(s.status, "value", "") == "occupied"]
        )
        warehouses = self._store.warehouses.list_all()
        wh_cap = sum(getattr(w, "capacity_tons", 0) or 0 for w in warehouses) or 1
        wh_used = sum(getattr(w, "used_tons", 0) or 0 for w in warehouses)
        eta = self._prediction.eta_accuracy()
        dwell = self._prediction.predict_dwell_time()
        invoices = self._store.invoices.count()
        revenue_proxy = float(invoices * 1000)

        kpis = [
            ExecutiveKPI("port_utilization", round(occupied / berths, 3), "ratio", "ok" if occupied / berths < 0.9 else "warn"),
            ExecutiveKPI("berth_occupancy", occupied, "berths"),
            ExecutiveKPI("terminal_load", self._store.terminals.count(), "terminals"),
            ExecutiveKPI("warehouse_capacity", round(wh_used / wh_cap, 3), "ratio"),
            ExecutiveKPI("container_dwell_time", dwell.value, "hours", "warn" if dwell.value > 48 else "ok"),
            ExecutiveKPI("average_turnaround", round(24 + yard_occ * 0.2, 1), "hours"),
            ExecutiveKPI("eta_accuracy", eta.value, "ratio"),
            ExecutiveKPI("revenue", revenue_proxy, "USD"),
            ExecutiveKPI("yard_density", round(yard_occ / slots, 3), "ratio"),
        ]
        return kpis

    def bottlenecks(self) -> list[dict]:
        items = []
        congestion = self._prediction.predict_congestion()
        if congestion.value >= 0.8:
            items.append({"type": "congestion", "severity": "critical", "value": congestion.value})
        elif congestion.value >= 0.6:
            items.append({"type": "congestion", "severity": "warning", "value": congestion.value})
        equipment = self._store.equipment.count()
        available = len(
            [
                e
                for e in self._store.equipment.list_all()
                if getattr(getattr(e, "status", None), "value", "") == "available"
            ]
        )
        if equipment and available / equipment < 0.3:
            items.append({"type": "equipment", "severity": "warning", "available_ratio": available / equipment})
        return items

    def dashboard(self) -> dict:
        return {
            "kpis": [k.to_dict() for k in self.kpis()],
            "bottlenecks": self.bottlenecks(),
            "twin": self._twin.state(),
        }


executive_dashboard_engine = ExecutiveDashboardEngine()
