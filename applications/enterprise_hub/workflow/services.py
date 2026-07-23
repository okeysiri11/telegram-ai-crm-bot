"""Workflow analytics, AI optimization, and dashboards."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class WorkflowOptimization:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def analyze(self, *, workflow_id: str) -> dict[str, Any]:
        wf = self.store.wf_definitions.get(workflow_id)
        if wf is None:
            raise NotFoundError(f"workflow not found: {workflow_id}")
        blocks = wf.get("blocks") or []
        suggestions = []
        if len(blocks) > 6:
            suggestions.append("remove_redundant_steps")
        notif = sum(1 for b in blocks if b.get("type") == "notification")
        if notif > 1:
            suggestions.append("merge_notifications")
        if any(b.get("type") == "approval" for b in blocks):
            suggestions.append("consider_auto_approval")
        suggestions.append("estimate_duration")
        suggestions.append("detect_bottleneck")
        oid = _id("wf_opt")
        return self.store.wf_optimizations.save(
            oid,
            {
                "optimization_id": oid,
                "workflow_id": workflow_id,
                "suggestions": suggestions,
                "estimated_duration_ms": max(50, len(blocks) * 25),
                "bottleneck": "approval" if any(b.get("type") == "approval" for b in blocks) else "none",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"optimizations": self.store.wf_optimizations.count()}


class WorkflowDashboard:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.types = list(DEFAULT_CONFIG.wf_dashboard_types)

    def render(self, *, dashboard_type: str) -> dict[str, Any]:
        dt = dashboard_type.lower().strip()
        if dt not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "performance": {
                "definitions": self.store.wf_definitions.count(),
                "executions": self.store.wf_executions.count(),
                "engine_runs": self.store.wf_engine_runs.count(),
            },
            "approvals": {
                "approvals": self.store.wf_approvals.count(),
            },
            "scheduler": {
                "schedules": self.store.wf_schedules.count(),
                "fires": self.store.wf_schedule_fires.count(),
            },
            "templates": {
                "templates": self.store.wf_templates.count(),
            },
            "optimization": {
                "optimizations": self.store.wf_optimizations.count(),
                "validations": self.store.wf_validations.count(),
            },
        }.get(dt, {})
        did = _id("wf_dash")
        return self.store.wf_dashboards.save(
            did,
            {
                "dashboard_id": did,
                "dashboard_type": dt,
                "metrics": metrics,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.wf_dashboards.count(), "types": self.types}
