"""Capability manager — Sprint 20.11."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.business_capabilities.capability_catalog import CapabilityCatalog
from applications.enterprise_hub.business_capabilities.capability_engine import CapabilityEngine
from applications.enterprise_hub.business_capabilities.capability_mapper import CapabilityMapper
from applications.enterprise_hub.business_capabilities.capability_registry import CapabilityRegistry
from applications.enterprise_hub.business_capabilities.dependency_engine import DependencyEngine
from applications.enterprise_hub.business_capabilities.impact_analysis import ImpactAnalysis
from applications.enterprise_hub.business_capabilities.maturity_engine import MaturityEngine
from applications.enterprise_hub.business_capabilities.strategy_alignment import StrategyAlignment
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class CapabilityManager:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.registry = CapabilityRegistry(self.store)
        self.catalog = CapabilityCatalog(self.store)
        self.mapper = CapabilityMapper(self.store)
        self.dependencies = DependencyEngine(self.store)
        self.strategy = StrategyAlignment(self.store)
        self.maturity = MaturityEngine(self.store)
        self.impact = ImpactAnalysis(self.store)
        self.engine = CapabilityEngine(self.store)

    def status(self) -> dict[str, Any]:
        return {
            "registry": self.registry.status(),
            "catalog": self.catalog.status(),
            "maps": self.mapper.status(),
            "dependencies": self.dependencies.status(),
            "strategy": self.strategy.status(),
            "maturity": self.maturity.status(),
            "impact": self.impact.status(),
            "advisor": self.engine.status(),
        }
