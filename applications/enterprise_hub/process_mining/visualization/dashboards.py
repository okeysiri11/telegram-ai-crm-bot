from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"



from applications.enterprise_hub.process_mining.analytics.efficiency import EfficiencyAnalytics
from applications.enterprise_hub.process_mining.analytics.kpi import ProcessKpi
from applications.enterprise_hub.process_mining.analytics.recommendations import RecommendationAnalytics
from applications.enterprise_hub.process_mining.analytics.sla import SlaAnalytics
from applications.enterprise_hub.process_mining.visualization.heatmap import Heatmap
from applications.enterprise_hub.process_mining.visualization.process_graph import ProcessGraph
from applications.enterprise_hub.process_mining.visualization.timeline import TimelineViz


class ExecutiveDashboard:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.kpi = ProcessKpi(self.store)
        self.efficiency = EfficiencyAnalytics(self.store)
        self.sla = SlaAnalytics(self.store)
        self.recs = RecommendationAnalytics(self.store)
        self.graph = ProcessGraph(self.store)
        self.heatmap = Heatmap(self.store)
        self.timeline = TimelineViz(self.store)

    def render(self, *, process_id: str) -> dict[str, Any]:
        kpi = self.kpi.report(process_id=process_id)
        eff = self.efficiency.report(process_id=process_id)
        sla = self.sla.report(process_id=process_id)
        rec = self.recs.report(process_id=process_id)
        graph = self.graph.render(process_id=process_id)
        heat = self.heatmap.render(process_id=process_id)
        tl = self.timeline.render(process_id=process_id)
        bn = [b for b in self.store.epm_bottlenecks.list_all() if b.get("process_id") == process_id]
        opts = [o for o in self.store.epm_optimizations.list_all() if o.get("process_id") == process_id]
        effect = (opts[-1].get("expected_effect") if opts else {}) or {}
        did = _id("epm_dash")
        return self.store.epm_dashboards.save(
            did,
            {
                "dashboard_id": did,
                "process_id": process_id,
                "process_map": graph,
                "department_load": heat.get("heat"),
                "bottlenecks": bn[-1]["bottlenecks"] if bn else [],
                "sla_breaches": sla.get("breaches"),
                "on_time_pct": sla.get("on_time_pct"),
                "dynamics": tl.get("events"),
                "ai_recommendations": rec.get("recommendations"),
                "expected_optimization_effect": effect,
                "kpi": kpi,
                "efficiency": eff.get("efficiency"),
                "at": _now(),
            },
        )
