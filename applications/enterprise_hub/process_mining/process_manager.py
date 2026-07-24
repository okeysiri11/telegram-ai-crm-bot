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



from applications.enterprise_hub.process_mining.bottleneck_detector import BottleneckDetector
from applications.enterprise_hub.process_mining.conformance_engine import ConformanceEngine
from applications.enterprise_hub.process_mining.event_collector import EventCollector
from applications.enterprise_hub.process_mining.event_normalizer import EventNormalizer
from applications.enterprise_hub.process_mining.mining.anomaly_detection import AnomalyDetection
from applications.enterprise_hub.process_mining.mining.performance import PerformanceMining
from applications.enterprise_hub.process_mining.mining.root_cause import RootCauseMining
from applications.enterprise_hub.process_mining.mining.variants import VariantMining
from applications.enterprise_hub.process_mining.optimization_engine import OptimizationEngine
from applications.enterprise_hub.process_mining.process_discovery import ProcessDiscovery
from applications.enterprise_hub.process_mining.process_repository import ProcessRepository
from applications.enterprise_hub.process_mining.process_simulator import ProcessSimulator
from applications.enterprise_hub.process_mining.process_versioning import ProcessVersioning


class ProcessManager:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
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

    def status(self) -> dict[str, Any]:
        return {
            "collector": self.collector.status(),
            "normalizer": self.normalizer.status(),
            "repository": self.repository.status(),
            "discovery": self.discovery.status(),
            "conformance": self.conformance.status(),
            "bottlenecks": self.bottlenecks.status(),
            "optimization": self.optimization.status(),
            "simulations": self.simulator.status(),
            "versions": self.versioning.status(),
        }
