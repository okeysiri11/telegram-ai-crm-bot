
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

from applications.enterprise_hub.business_capabilities.capability_engine import CapabilityEngine
from applications.enterprise_hub.business_capabilities.capability_registry import CapabilityRegistry
from applications.enterprise_hub.business_capabilities.maturity_engine import MaturityEngine


class RoadmapViz:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.registry = CapabilityRegistry(self.store)
        self.maturity = MaturityEngine(self.store)
        self.advisor = CapabilityEngine(self.store)

    def generate(self, horizon_quarters: int = 8) -> dict[str, Any]:
        items = self.registry.list_all()
        if not items:
            raise ValidationError("no capabilities for roadmap")
        assessment = self.maturity.assess()
        advice = self.advisor.advise(limit=8)
        phases = []
        for q in range(1, max(1, int(horizon_quarters)) + 1):
            slice_advice = advice["recommendations"][(q - 1) % len(advice["recommendations"])]
            phases.append(
                {
                    "quarter": f"Q{q}",
                    "focus": slice_advice["capability_key"],
                    "action": slice_advice["action"],
                    "investment": round(0.5 + slice_advice["expected_roi"], 2),
                    "target_maturity": min(5, int(slice_advice["maturity_level"]) + 1),
                }
            )
        rid = _id("ebc_road")
        record = {
            "roadmap_id": rid,
            "current_state": {"average_maturity": assessment["average_maturity"]},
            "target_state": {"average_maturity": min(5.0, assessment["average_maturity"] + 1.0)},
            "phases": phases,
            "dependencies": [d for d in self.store.ebc_dependencies.list_all()][:20],
            "generated_at": _now(),
        }
        self.store.ebc_roadmaps.save(rid, record)
        return record
