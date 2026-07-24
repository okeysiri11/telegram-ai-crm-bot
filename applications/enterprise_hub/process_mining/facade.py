"""Process Mining Suite facade — Sprint 20.10."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.process_mining.analytics.efficiency import EfficiencyAnalytics
from applications.enterprise_hub.process_mining.analytics.kpi import ProcessKpi
from applications.enterprise_hub.process_mining.analytics.recommendations import RecommendationAnalytics
from applications.enterprise_hub.process_mining.analytics.sla import SlaAnalytics
from applications.enterprise_hub.process_mining.bottleneck_detector import BottleneckDetector
from applications.enterprise_hub.process_mining.conformance_engine import ConformanceEngine
from applications.enterprise_hub.process_mining.event_collector import EventCollector
from applications.enterprise_hub.process_mining.event_normalizer import EventNormalizer
from applications.enterprise_hub.process_mining.mining.anomaly_detection import AnomalyDetection
from applications.enterprise_hub.process_mining.mining.performance import PerformanceMining
from applications.enterprise_hub.process_mining.mining.root_cause import RootCauseMining
from applications.enterprise_hub.process_mining.mining.variants import VariantMining
from applications.enterprise_hub.process_mining.models import DEFAULT_REFERENCE_STEPS, INTEGRATION_TARGETS
from applications.enterprise_hub.process_mining.optimization_engine import OptimizationEngine
from applications.enterprise_hub.process_mining.process_discovery import ProcessDiscovery
from applications.enterprise_hub.process_mining.process_manager import ProcessManager
from applications.enterprise_hub.process_mining.process_repository import ProcessRepository
from applications.enterprise_hub.process_mining.process_simulator import ProcessSimulator
from applications.enterprise_hub.process_mining.process_versioning import ProcessVersioning
from applications.enterprise_hub.process_mining.visualization.dashboards import ExecutiveDashboard
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class ProcessMiningSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.manager = ProcessManager(self.store)
        self.collector = EventCollector(self.store)
        self.normalizer = EventNormalizer(self.store)
        self.repository = ProcessRepository(self.store)
        self.discovery = ProcessDiscovery(self.store)
        self.conformance = ConformanceEngine(self.store)
        self.bottlenecks = BottleneckDetector(self.store)
        self.optimization = OptimizationEngine(self.store)
        self.simulator = ProcessSimulator(self.store)
        self.versioning = ProcessVersioning(self.store)
        self.performance = PerformanceMining(self.store)
        self.variants = VariantMining(self.store)
        self.root_cause = RootCauseMining(self.store)
        self.anomalies = AnomalyDetection(self.store)
        self.kpi = ProcessKpi(self.store)
        self.efficiency = EfficiencyAnalytics(self.store)
        self.sla = SlaAnalytics(self.store)
        self.recommendations = RecommendationAnalytics(self.store)
        self.dashboard = ExecutiveDashboard(self.store)

    def integrations(self) -> dict[str, Any]:
        return {"targets": list(INTEGRATION_TARGETS), "linked": True}

    def bootstrap(self) -> dict[str, Any]:
        # Seed multi-source events for multiple cases / variants
        seed = [
            # case A — standard
            {"source": "crm", "activity": "create_request", "case_id": "C1", "actor": "sales"},
            {"source": "workflow", "activity": "validate", "case_id": "C1", "actor": "ops"},
            {"source": "workflow", "activity": "approve", "case_id": "C1", "actor": "mgr"},
            {"source": "erp", "activity": "pay", "case_id": "C1", "actor": "finance"},
            {"source": "erp", "activity": "ship", "case_id": "C1", "actor": "logistics"},
            {"source": "crm", "activity": "close", "case_id": "C1", "actor": "sales"},
            # case B — standard (x2 weight via more cases)
            {"source": "crm", "activity": "create_request", "case_id": "C2", "actor": "sales"},
            {"source": "workflow", "activity": "validate", "case_id": "C2", "actor": "ops"},
            {"source": "workflow", "activity": "approve", "case_id": "C2", "actor": "mgr"},
            {"source": "erp", "activity": "pay", "case_id": "C2", "actor": "finance"},
            {"source": "erp", "activity": "ship", "case_id": "C2", "actor": "logistics"},
            {"source": "crm", "activity": "close", "case_id": "C2", "actor": "sales"},
            # case C — accelerated (skip validate)
            {"source": "crm", "activity": "create_request", "case_id": "C3", "actor": "sales"},
            {"source": "workflow", "activity": "approve", "case_id": "C3", "actor": "mgr"},
            {"source": "erp", "activity": "pay", "case_id": "C3", "actor": "finance"},
            {"source": "erp", "activity": "ship", "case_id": "C3", "actor": "logistics"},
            {"source": "crm", "activity": "close", "case_id": "C3", "actor": "sales"},
            # case D — nonstandard with rework/cycle
            {"source": "crm", "activity": "create_request", "case_id": "C4", "actor": "sales"},
            {"source": "workflow", "activity": "validate", "case_id": "C4", "actor": "ops"},
            {"source": "workflow", "activity": "approve", "case_id": "C4", "actor": "mgr"},
            {"source": "workflow", "activity": "approve", "case_id": "C4", "actor": "dir"},
            {"source": "erp", "activity": "pay", "case_id": "C4", "actor": "finance"},
            {"source": "ai_agents", "activity": "extra_review", "case_id": "C4", "actor": "ai"},
            {"source": "erp", "activity": "ship", "case_id": "C4", "actor": "logistics"},
            {"source": "documents", "activity": "close", "case_id": "C4", "actor": "clerk"},
            # more standard cases to dominate share
            {"source": "event_bus", "activity": "create_request", "case_id": "C5", "actor": "bus"},
            {"source": "workflow", "activity": "validate", "case_id": "C5", "actor": "ops"},
            {"source": "workflow", "activity": "approve", "case_id": "C5", "actor": "mgr"},
            {"source": "erp", "activity": "pay", "case_id": "C5", "actor": "finance"},
            {"source": "erp", "activity": "ship", "case_id": "C5", "actor": "logistics"},
            {"source": "crm", "activity": "close", "case_id": "C5", "actor": "sales"},
            {"source": "integrations", "activity": "create_request", "case_id": "C6", "actor": "ext"},
            {"source": "workflow", "activity": "validate", "case_id": "C6", "actor": "ops"},
            {"source": "workflow", "activity": "approve", "case_id": "C6", "actor": "mgr"},
            {"source": "erp", "activity": "pay", "case_id": "C6", "actor": "finance"},
            {"source": "erp", "activity": "ship", "case_id": "C6", "actor": "logistics"},
            {"source": "user_actions", "activity": "close", "case_id": "C6", "actor": "user"},
        ]
        # stamp increasing timestamps
        for i, e in enumerate(seed):
            e["ts"] = f"2026-07-24T09:{i:02d}:00+00:00"
        collected = self.collector.collect_batch(seed)
        normalized = self.normalizer.normalize()
        disc = self.discovery.discover(name="order-to-cash")
        process_id = disc["process_id"]
        ver = self.versioning.snapshot(process_id=process_id, label="discovered-v1")
        conf = self.conformance.check(process_id=process_id, reference_steps=list(DEFAULT_REFERENCE_STEPS))
        bn = self.bottlenecks.detect(process_id=process_id)
        perf = self.performance.analyze(process_id=process_id)
        var = self.variants.analyze(process_id=process_id)
        rc = self.root_cause.analyze(process_id=process_id, conformance_id=conf["conformance_id"])
        anom = self.anomalies.detect(process_id=process_id)
        opt = self.optimization.optimize(process_id=process_id, bottleneck_id=bn["bottleneck_id"])
        sim = self.simulator.simulate(process_id=process_id, optimization_id=opt["optimization_id"], cases=200)
        dash = self.dashboard.render(process_id=process_id)

        return {
            "bootstrap": True,
            "events_collected": len(collected),
            "events_normalized": len(normalized),
            "discovery_id": disc["discovery_id"],
            "process_id": process_id,
            "version_id": ver["version_id"],
            "conformance_id": conf["conformance_id"],
            "conformance_score": conf["conformance_score"],
            "bottleneck_id": bn["bottleneck_id"],
            "performance_id": perf["performance_id"],
            "variant_analysis_id": var["analysis_id"],
            "variant_count": var["variant_count"],
            "root_cause_id": rc["analysis_id"],
            "top_cause": rc["top_cause"],
            "anomaly_id": anom["anomaly_id"],
            "optimization_id": opt["optimization_id"],
            "simulation_id": sim["simulation_id"],
            "dashboard_id": dash["dashboard_id"],
            "sla_breaches": dash.get("sla_breaches"),
            "expected_effect": dash.get("expected_optimization_effect"),
            "integrations": self.integrations(),
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return self.manager.status()


process_mining = ProcessMiningSuite()
