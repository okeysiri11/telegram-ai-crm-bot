"""Meta knowledge bases and executive dashboards — AI Agents."""

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


class AgentMetaKnowledge:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.bases = list(DEFAULT_CONFIG.aa_knowledge_bases)

    def publish(self, *, base: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        b = base.lower().strip()
        if b not in self.bases:
            raise ValidationError(f"base must be one of {self.bases}")
        if not key:
            raise ValidationError("key required")
        eid = _id("aa_kg")
        return self.store.aa_knowledge.save(
            eid,
            {
                "entry_id": eid,
                "base": b,
                "key": key,
                "payload": payload or {},
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"entries": self.store.aa_knowledge.count(), "bases": self.bases}


class AgentDashboard:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.types = list(DEFAULT_CONFIG.aa_dashboard_types)

    def render(self, *, dashboard_type: str) -> dict[str, Any]:
        dt = dashboard_type.lower().strip()
        if dt not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "agents": {
                "agents": self.store.aa_agents.count(),
                "capabilities": self.store.aa_capabilities.count(),
                "versions": self.store.aa_versions.count(),
            },
            "automation": {
                "automations": self.store.aa_automations.count(),
                "approvals": self.store.aa_approvals.count(),
                "hitl": self.store.aa_hitl.count(),
                "emergency_stops": self.store.aa_emergency_stops.count(),
            },
            "execution": {
                "tasks": self.store.aa_tasks.count(),
                "executions": self.store.aa_executions.count(),
                "retries": self.store.aa_retries.count(),
            },
            "performance": {
                "metrics": self.store.aa_metrics.count(),
                "insights": self.store.aa_insights.count(),
                "feedback": self.store.aa_feedback.count(),
            },
            "governance": {
                "health": self.store.aa_health.count(),
                "audit": self.store.aa_audit.count(),
                "security": self.store.aa_security.count(),
                "permission_checks": self.store.aa_permission_checks.count(),
            },
        }.get(dt, {})
        did = _id("aa_dash")
        return self.store.aa_dashboards.save(
            did,
            {
                "dashboard_id": did,
                "dashboard_type": dt,
                "metrics": metrics,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.aa_dashboards.count(), "types": self.types}
