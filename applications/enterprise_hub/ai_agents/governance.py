"""Monitoring & governance — health, metrics, audit, security, permissions, resources."""

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


class AgentGovernance:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def health_check(self, *, agent_id: str) -> dict[str, Any]:
        agent = self.store.aa_agents.get(agent_id)
        if agent is None:
            raise NotFoundError(f"agent not found: {agent_id}")
        hid = _id("aa_health")
        return self.store.aa_health.save(
            hid,
            {
                "health_id": hid,
                "agent_id": agent_id,
                "lifecycle": agent.get("lifecycle", "unknown"),
                "status": "healthy" if agent.get("lifecycle") == "active" else "degraded",
                "at": _now(),
            },
        )

    def metrics(self, *, agent_id: str, latency_ms: float = 0.0, success_rate: float = 1.0) -> dict[str, Any]:
        if self.store.aa_agents.get(agent_id) is None:
            raise NotFoundError(f"agent not found: {agent_id}")
        mid = _id("aa_metric")
        return self.store.aa_metrics.save(
            mid,
            {
                "metric_id": mid,
                "agent_id": agent_id,
                "latency_ms": float(latency_ms),
                "success_rate": float(success_rate),
                "at": _now(),
            },
        )

    def audit(self, *, action: str, actor: str = "system", detail: str = "") -> dict[str, Any]:
        if not action:
            raise ValidationError("action required")
        aid = _id("aa_audit")
        return self.store.aa_audit.save(
            aid,
            {
                "audit_id": aid,
                "action": action,
                "actor": actor,
                "detail": detail,
                "at": _now(),
            },
        )

    def security_event(self, *, agent_id: str, severity: str = "info", detail: str = "") -> dict[str, Any]:
        sid = _id("aa_sec")
        return self.store.aa_security.save(
            sid,
            {
                "security_id": sid,
                "agent_id": agent_id,
                "severity": severity,
                "detail": detail,
                "at": _now(),
            },
        )

    def validate_permission(self, *, agent_id: str, permission: str) -> dict[str, Any]:
        agent = self.store.aa_agents.get(agent_id)
        if agent is None:
            raise NotFoundError(f"agent not found: {agent_id}")
        if not permission:
            raise ValidationError("permission required")
        allowed = permission in (agent.get("permissions") or [])
        vid = _id("aa_pval")
        return self.store.aa_permission_checks.save(
            vid,
            {
                "check_id": vid,
                "agent_id": agent_id,
                "permission": permission,
                "allowed": allowed,
                "at": _now(),
            },
        )

    def track_resources(self, *, agent_id: str, cpu: float = 0.0, memory_mb: float = 0.0) -> dict[str, Any]:
        if self.store.aa_agents.get(agent_id) is None:
            raise NotFoundError(f"agent not found: {agent_id}")
        rid = _id("aa_res")
        return self.store.aa_resources.save(
            rid,
            {
                "resource_id": rid,
                "agent_id": agent_id,
                "cpu": float(cpu),
                "memory_mb": float(memory_mb),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "health": self.store.aa_health.count(),
            "metrics": self.store.aa_metrics.count(),
            "audit": self.store.aa_audit.count(),
            "security": self.store.aa_security.count(),
            "permission_checks": self.store.aa_permission_checks.count(),
            "resources": self.store.aa_resources.count(),
        }
