"""Orchestrator dashboards and knowledge graph."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class OrchestratorKnowledge:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.bases = list(DEFAULT_CONFIG.orch_knowledge_bases)

    def publish(self, *, base: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if base not in self.bases:
            raise ValidationError(f"base must be one of {self.bases}")
        if not key:
            raise ValidationError("key required")
        eid = _id("orch_kg")
        return self.store.orch_knowledge.save(
            eid,
            {
                "entry_id": eid,
                "base": base,
                "key": key,
                "payload": payload or {},
                "graph_node": f"orch:{base}:{key}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"entries": self.store.orch_knowledge.count(), "bases": self.bases}


class OrchestratorDashboard:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.types = list(DEFAULT_CONFIG.orch_dashboard_types)

    def render(self, *, dashboard_type: str = "orchestrator") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "orchestrator": {
                "workflows": self.store.orch_workflows.count(),
                "executions": self.store.orch_executions.count(),
                "intents": self.store.orch_intents.count(),
            },
            "workflow": {
                "workflows": self.store.orch_workflows.count(),
                "templates": self.store.orch_templates.count(),
                "approvals": self.store.orch_approvals.count(),
            },
            "execution": {
                "executions": self.store.orch_executions.count(),
                "retries": self.store.orch_retries.count(),
                "rollbacks": self.store.orch_rollbacks.count(),
                "monitors": self.store.orch_monitors.count(),
            },
            "platform_activity": {
                "routes": self.store.orch_routes.count(),
                "coordinations": self.store.orch_coordinations.count(),
            },
            "ai_decision": {
                "decisions": self.store.orch_decisions.count(),
                "explanations": self.store.orch_explanations.count(),
            },
        }[dashboard_type]
        did = _id("orch_dash")
        return self.store.orch_dashboards.save(
            did,
            {
                "dashboard_id": did,
                "dashboard_type": dashboard_type,
                "metrics": metrics,
                "generated_at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.orch_dashboards.count(), "types": self.types}
