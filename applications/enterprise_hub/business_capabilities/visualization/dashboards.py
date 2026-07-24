
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

from applications.enterprise_hub.business_capabilities.analytics.performance import PerformanceAnalytics
from applications.enterprise_hub.business_capabilities.analytics.strategy import StrategyAnalytics
from applications.enterprise_hub.business_capabilities.capability_engine import CapabilityEngine
from applications.enterprise_hub.business_capabilities.capability_mapper import CapabilityMapper
from applications.enterprise_hub.business_capabilities.maturity_engine import MaturityEngine
from applications.enterprise_hub.business_capabilities.visualization.heatmap import HeatmapViz
from applications.enterprise_hub.business_capabilities.visualization.roadmap import RoadmapViz


class ExecutiveCapabilityDashboard:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.mapper = CapabilityMapper(self.store)
        self.maturity = MaturityEngine(self.store)
        self.advisor = CapabilityEngine(self.store)
        self.performance = PerformanceAnalytics(self.store)
        self.strategy = StrategyAnalytics(self.store)
        self.heatmap = HeatmapViz(self.store)
        self.roadmap = RoadmapViz(self.store)

    def render(self) -> dict[str, Any]:
        cmap = self.mapper.hierarchy()
        mat = self.maturity.assess()
        advice = self.advisor.advise()
        perf = self.performance.report()
        strat = self.strategy.report()
        heat = self.heatmap.render()
        road = self.roadmap.generate()
        did = _id("ebc_dash")
        record = {
            "dashboard_id": did,
            "capability_map_id": cmap["map_id"],
            "enterprise_maturity": mat["average_maturity"],
            "strategic_risks": strat["strategic_risks"],
            "ai_recommendations": advice["recommendations"][:5],
            "kpi_rows": perf["rows"][:10],
            "heatmap_id": heat["viz_id"],
            "roadmap_id": road["roadmap_id"],
            "forecast": road["target_state"],
            "rendered_at": _now(),
        }
        self.store.ebc_dashboards.save(did, record)
        return record
