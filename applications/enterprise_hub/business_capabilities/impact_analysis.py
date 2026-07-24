
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

from applications.enterprise_hub.business_capabilities.capability_registry import CapabilityRegistry
from applications.enterprise_hub.business_capabilities.dependency_engine import DependencyEngine


class ImpactAnalysis:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.registry = CapabilityRegistry(self.store)
        self.dependencies = DependencyEngine(self.store)

    def analyze(self, capability_key: str, change: str = "process_change") -> dict[str, Any]:
        cap = self.registry.require_key(capability_key)
        downstream = self.dependencies.downstream(capability_key)
        chain = [
            {"stage": "source", "capability_key": capability_key, "effect": change},
            *[{"stage": "downstream", "capability_key": k, "effect": "affected"} for k in downstream],
        ]
        # classic impact narrative stages
        narrative = [
            f"Change in {capability_key}",
            *[f"Impact on {k}" for k in downstream[:4]],
            "Impact on timelines",
            "Impact on profit",
            "Impact on customers",
        ]
        severity = min(1.0, 0.2 + 0.1 * len(downstream) + (5 - int(cap.get("maturity_level", 3))) * 0.05)
        iid = _id("ebc_impact")
        record = {
            "impact_id": iid,
            "capability_key": capability_key,
            "change": change,
            "downstream": downstream,
            "chain": chain,
            "narrative": narrative,
            "severity_score": round(severity, 2),
            "analyzed_at": _now(),
        }
        self.store.ebc_impacts.save(iid, record)
        return record

    def status(self) -> dict[str, Any]:
        return {"impacts": len(self.store.ebc_impacts.list_all())}
