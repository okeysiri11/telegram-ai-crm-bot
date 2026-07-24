"""Business Capability Suite facade — Sprint 20.11."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.business_capabilities.analytics.dependencies import DependencyAnalytics
from applications.enterprise_hub.business_capabilities.analytics.maturity import MaturityAnalytics
from applications.enterprise_hub.business_capabilities.analytics.performance import PerformanceAnalytics
from applications.enterprise_hub.business_capabilities.analytics.strategy import StrategyAnalytics
from applications.enterprise_hub.business_capabilities.capabilities import DEFAULT_DEPENDENCIES
from applications.enterprise_hub.business_capabilities.capability_catalog import CapabilityCatalog
from applications.enterprise_hub.business_capabilities.capability_engine import CapabilityEngine
from applications.enterprise_hub.business_capabilities.capability_manager import CapabilityManager
from applications.enterprise_hub.business_capabilities.capability_mapper import CapabilityMapper
from applications.enterprise_hub.business_capabilities.capability_registry import CapabilityRegistry
from applications.enterprise_hub.business_capabilities.dependency_engine import DependencyEngine
from applications.enterprise_hub.business_capabilities.impact_analysis import ImpactAnalysis
from applications.enterprise_hub.business_capabilities.maturity_engine import MaturityEngine
from applications.enterprise_hub.business_capabilities.models import INTEGRATION_TARGETS
from applications.enterprise_hub.business_capabilities.strategy_alignment import StrategyAlignment
from applications.enterprise_hub.business_capabilities.visualization.capability_map import CapabilityMapViz
from applications.enterprise_hub.business_capabilities.visualization.dashboards import ExecutiveCapabilityDashboard
from applications.enterprise_hub.business_capabilities.visualization.heatmap import HeatmapViz
from applications.enterprise_hub.business_capabilities.visualization.hierarchy import HierarchyViz
from applications.enterprise_hub.business_capabilities.visualization.roadmap import RoadmapViz
from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class BusinessCapabilitySuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.manager = CapabilityManager(self.store)
        self.registry = CapabilityRegistry(self.store)
        self.catalog = CapabilityCatalog(self.store)
        self.mapper = CapabilityMapper(self.store)
        self.dependencies = DependencyEngine(self.store)
        self.strategy = StrategyAlignment(self.store)
        self.maturity = MaturityEngine(self.store)
        self.impact = ImpactAnalysis(self.store)
        self.engine = CapabilityEngine(self.store)
        self.maturity_analytics = MaturityAnalytics(self.store)
        self.dependency_analytics = DependencyAnalytics(self.store)
        self.performance = PerformanceAnalytics(self.store)
        self.strategy_analytics = StrategyAnalytics(self.store)
        self.map_viz = CapabilityMapViz(self.store)
        self.hierarchy_viz = HierarchyViz(self.store)
        self.heatmap = HeatmapViz(self.store)
        self.roadmap = RoadmapViz(self.store)
        self.dashboard = ExecutiveCapabilityDashboard(self.store)

    def integrations(self) -> dict[str, Any]:
        return {"targets": list(INTEGRATION_TARGETS), "linked": True}

    def bootstrap(self) -> dict[str, Any]:
        seeded = self.catalog.seed()
        # link default dependency chain (skip missing keys safely)
        linked = 0
        for src, tgt in DEFAULT_DEPENDENCIES:
            if self.registry.find_by_key(src) and self.registry.find_by_key(tgt):
                self.dependencies.link(src, tgt)
                linked += 1
        hierarchy = self.mapper.hierarchy(root_key="enterprise")
        # strategy alignments for core domains
        for key, strategy in (
            ("finance", "Improve cash conversion cycle"),
            ("sales", "Grow revenue pipeline"),
            ("maritime", "Optimize port throughput"),
            ("ai_operations", "Scale AI-driven operations"),
        ):
            if self.registry.find_by_key(key):
                self.strategy.align(
                    capability_key=key,
                    strategy=strategy,
                    goals=[f"Goal for {key}"],
                    okrs=[f"OKR-{key}-1"],
                    projects=[f"project-{key}"],
                    investments=[f"capex-{key}"],
                )
        maturity = self.maturity.assess()
        impact = self.impact.analyze("procurement", change="procurement_process_change")
        advice = self.engine.advise()
        perf = self.performance.report()
        road = self.roadmap.generate()
        dash = self.dashboard.render()
        return {
            "bootstrap": True,
            "catalog_id": seeded["catalog_id"],
            "capabilities_seeded": seeded["seeded"],
            "capabilities_total": seeded["total"],
            "dependencies_linked": linked,
            "map_id": hierarchy["map_id"],
            "maturity_assessment_id": maturity["assessment_id"],
            "average_maturity": maturity["average_maturity"],
            "impact_id": impact["impact_id"],
            "impact_severity": impact["severity_score"],
            "advice_id": advice["advice_id"],
            "recommendation_count": advice["count"],
            "performance_id": perf["analytics_id"],
            "roadmap_id": road["roadmap_id"],
            "dashboard_id": dash["dashboard_id"],
            "enterprise_maturity": dash["enterprise_maturity"],
            "integrations": self.integrations(),
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return self.manager.status()


business_capabilities = BusinessCapabilitySuite()
