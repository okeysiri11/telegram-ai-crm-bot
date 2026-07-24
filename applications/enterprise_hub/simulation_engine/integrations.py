"""Integration bridges — Digital Twin, Knowledge, Data Fabric, Event Bus, Workflow, AOP, Rules."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store
from applications.enterprise_hub.simulation_engine.models import INTEGRATION_TARGETS


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class SimulationIntegrations:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def connect(self, *, target: str, ref_id: str = "", payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if target not in INTEGRATION_TARGETS:
            raise ValidationError(f"invalid integration target: {target}")
        iid = _id("esi_int")
        return self.store.esi_integrations.save(
            iid,
            {
                "integration_id": iid,
                "target": target,
                "ref_id": ref_id,
                "payload": payload or {},
                "status": "connected",
                "at": _now(),
            },
        )

    def bootstrap_links(self) -> dict[str, Any]:
        links = [
            self.connect(target="digital_twin", ref_id="prediction_context", payload={"use": "state_snapshot"}),
            self.connect(target="knowledge_platform", ref_id="rag", payload={"use": "prior_cases"}),
            self.connect(target="data_fabric", ref_id="unified_query", payload={"use": "federated_metrics"}),
            self.connect(target="event_bus", ref_id="enterprise.sim.trigger", payload={"use": "event_driven_runs"}),
            self.connect(target="workflow", ref_id="approval", payload={"use": "decision_handoff"}),
            self.connect(target="ai_orchestrator", ref_id="plan", payload={"use": "multi_agent_eval"}),
            self.connect(target="business_rules", ref_id="policy", payload={"use": "constraint_guardrails"}),
        ]
        return {
            "linked": len(links),
            "integration_ids": [l["integration_id"] for l in links],
            "targets": [l["target"] for l in links],
        }

    def status(self) -> dict[str, Any]:
        items = self.store.esi_integrations.list_all()
        return {
            "integrations": len(items),
            "targets": sorted({i.get("target") for i in items}),
        }
