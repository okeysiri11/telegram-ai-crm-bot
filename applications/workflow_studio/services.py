"""Business templates + Enterprise features + Monitoring (Sprint 12.2)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.workflow_studio.config import DEFAULT_CONFIG
from applications.workflow_studio.editor import VisualEditor, visual_editor
from applications.workflow_studio.shared.exceptions import NotFoundError, ValidationError
from applications.workflow_studio.shared.store import WorkflowStudioStore, workflow_studio_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


TEMPLATE_NODES = {
    "crm": ["webhook", "ai_agent", "condition", "notification"],
    "erp": ["api", "database", "condition", "approval", "notification"],
    "accounting": ["api", "condition", "approval", "database"],
    "drone_mission": ["scheduler", "ai_agent", "api", "decision", "notification"],
    "drone_manufacturing": ["scheduler", "tool", "condition", "approval", "notification"],
    "construction": ["human_task", "approval", "file", "notification"],
    "auto_marketplace": ["webhook", "llm", "condition", "api", "notification"],
    "agro_marketplace": ["webhook", "ai_agent", "condition", "notification"],
    "legal": ["file", "llm", "approval", "notification"],
    "finance": ["api", "condition", "approval", "database", "notification"],
    "hr": ["webhook", "human_task", "approval", "notification"],
    "customer_support": ["webhook", "llm", "condition", "human_task", "notification"],
    "sales_pipeline": ["webhook", "ai_agent", "condition", "notification", "database"],
}


class BusinessTemplates:
    def __init__(self, store: WorkflowStudioStore | None = None, editor: VisualEditor | None = None) -> None:
        self.store = store or workflow_studio_store
        self.editor = editor or visual_editor
        self.keys = list(DEFAULT_CONFIG.business_template_keys)

    def list_templates(self) -> list[dict[str, Any]]:
        return [{"key": k, "nodes": TEMPLATE_NODES.get(k, [])} for k in self.keys]

    def instantiate(self, *, key: str, name: str = "") -> dict[str, Any]:
        if key not in self.keys:
            raise ValidationError(f"unknown template key: {key}")
        seq = TEMPLATE_NODES.get(key) or ["webhook", "notification"]
        wf = self.editor.create_workflow(name=name or f"{key.replace('_', ' ').title()} Flow", template_key=key)
        nodes = []
        x = 0.0
        for ntype in seq:
            nodes.append(self.editor.add_node(wf["workflow_id"], node_type=ntype, x=x, y=40))
            x += 150
        for i in range(len(nodes) - 1):
            self.editor.connect(wf["workflow_id"], source_id=nodes[i]["node_id"], target_id=nodes[i + 1]["node_id"])
        self.store.templates.save(key, {"key": key, "workflow_id": wf["workflow_id"], "at": _now()})
        return {"template_key": key, "workflow": wf, "nodes": nodes}

    def status(self) -> dict[str, Any]:
        return {"business_templates": "1.0", "templates": len(self.keys), "ready": True}


class EnterpriseWorkflow:
    def __init__(self, store: WorkflowStudioStore | None = None, editor: VisualEditor | None = None) -> None:
        self.store = store or workflow_studio_store
        self.editor = editor or visual_editor

    def save_version(self, workflow_id: str, *, author: str = "") -> dict[str, Any]:
        wf = self.editor.get_workflow(workflow_id)
        vid = f"ver_{uuid.uuid4().hex[:10]}"
        snap = {
            "version_id": vid,
            "workflow_id": workflow_id,
            "version": wf.get("version", 1),
            "node_ids": list(wf.get("node_ids") or []),
            "connection_ids": list(wf.get("connection_ids") or []),
            "author": author,
            "at": _now(),
        }
        self.store.versions.save(vid, snap)
        wf["version"] = int(wf.get("version", 1)) + 1
        wf["updated_at"] = _now()
        self.store.workflows.save(workflow_id, wf)
        return snap

    def version_history(self, workflow_id: str) -> list[dict[str, Any]]:
        return [v for v in self.store.versions.list_all() if v.get("workflow_id") == workflow_id]

    def compare(self, version_a: str, version_b: str) -> dict[str, Any]:
        a = self.store.versions.get(version_a)
        b = self.store.versions.get(version_b)
        if not a or not b:
            raise NotFoundError("version", version_a if not a else version_b)
        return {
            "a": version_a,
            "b": version_b,
            "nodes_added": list(set(b.get("node_ids", [])) - set(a.get("node_ids", []))),
            "nodes_removed": list(set(a.get("node_ids", [])) - set(b.get("node_ids", []))),
        }

    def merge(self, workflow_id: str, *, from_version_id: str) -> dict[str, Any]:
        snap = self.store.versions.get(from_version_id)
        if snap is None:
            raise NotFoundError("version", from_version_id)
        wf = self.editor.get_workflow(workflow_id)
        wf["node_ids"] = list(dict.fromkeys([*wf.get("node_ids", []), *snap.get("node_ids", [])]))
        wf["connection_ids"] = list(dict.fromkeys([*wf.get("connection_ids", []), *snap.get("connection_ids", [])]))
        wf["updated_at"] = _now()
        self.store.workflows.save(workflow_id, wf)
        return {"workflow_id": workflow_id, "merged_from": from_version_id, "node_count": len(wf["node_ids"])}

    def set_permissions(self, workflow_id: str, *, principal: str, role: str) -> dict[str, Any]:
        if role not in {"owner", "editor", "viewer"}:
            raise ValidationError("role must be owner|editor|viewer")
        pid = f"perm_{uuid.uuid4().hex[:8]}"
        row = {"permission_id": pid, "workflow_id": workflow_id, "principal": principal, "role": role, "at": _now()}
        self.store.permissions.save(pid, row)
        return row

    def share(self, workflow_id: str, *, with_org_id: str = "", with_user: str = "") -> dict[str, Any]:
        sid = f"share_{uuid.uuid4().hex[:8]}"
        row = {"share_id": sid, "workflow_id": workflow_id, "org_id": with_org_id, "user": with_user, "at": _now()}
        self.store.shares.save(sid, row)
        return row

    def organization_library(self, org_id: str) -> dict[str, Any]:
        shared = [s for s in self.store.shares.list_all() if s.get("org_id") == org_id]
        return {"org_id": org_id, "shared": shared, "count": len(shared)}

    def multi_user_lock(self, workflow_id: str, *, user_id: str) -> dict[str, Any]:
        key = f"lock:{workflow_id}"
        existing = self.store.permissions.get(key)
        if existing and existing.get("user_id") != user_id:
            return {"locked": True, "by": existing.get("user_id"), "acquired": False}
        lock = {"permission_id": key, "workflow_id": workflow_id, "user_id": user_id, "role": "lock", "at": _now()}
        self.store.permissions.save(key, lock)
        return {"locked": True, "by": user_id, "acquired": True}

    def status(self) -> dict[str, Any]:
        return {
            "enterprise": "1.0",
            "versions": len(self.store.versions.list_all()),
            "shares": len(self.store.shares.list_all()),
            "ready": True,
        }


class WorkflowMonitoring:
    def __init__(self, store: WorkflowStudioStore | None = None) -> None:
        self.store = store or workflow_studio_store

    def record_metrics(self, execution: dict[str, Any]) -> dict[str, Any]:
        mid = execution.get("execution_id") or f"met_{uuid.uuid4().hex[:8]}"
        success = execution.get("status") == "completed"
        row = {
            "metric_id": mid,
            "workflow_id": execution.get("workflow_id"),
            "execution_id": execution.get("execution_id"),
            "success": success,
            "steps": len(execution.get("timeline") or []),
            "errors": len(execution.get("errors") or []),
            "at": _now(),
        }
        self.store.metrics.save(mid, row)
        return row

    def execution_metrics(self, workflow_id: str | None = None) -> dict[str, Any]:
        rows = self.store.metrics.list_all()
        if workflow_id:
            rows = [r for r in rows if r.get("workflow_id") == workflow_id]
        total = len(rows) or 1
        success = sum(1 for r in rows if r.get("success"))
        return {
            "count": len(rows),
            "success_rate": round(success / total, 3) if rows else 0.0,
            "failures": sum(1 for r in rows if not r.get("success")),
            "avg_steps": round(sum(r.get("steps", 0) for r in rows) / total, 2) if rows else 0,
        }

    def performance_dashboard(self) -> dict[str, Any]:
        return {"type": "performance_dashboard", "metrics": self.execution_metrics(), "at": _now()}

    def failure_analysis(self) -> dict[str, Any]:
        failed = [e for e in self.store.executions.list_all() if e.get("status") == "failed"]
        reasons: dict[str, int] = {}
        for exe in failed:
            for err in exe.get("errors") or []:
                key = err.get("error", "unknown")
                reasons[key] = reasons.get(key, 0) + 1
        return {"failed_executions": len(failed), "reasons": reasons}

    def execution_heatmap(self, workflow_id: str) -> dict[str, Any]:
        rows = [r for r in self.store.metrics.list_all() if r.get("workflow_id") == workflow_id]
        return {
            "workflow_id": workflow_id,
            "cells": [{"execution_id": r.get("execution_id"), "success": r.get("success"), "steps": r.get("steps")} for r in rows],
            "count": len(rows),
        }

    def status(self) -> dict[str, Any]:
        return {"monitoring": "1.0", "metrics": len(self.store.metrics.list_all()), "ready": True}


business_templates = BusinessTemplates()
enterprise_workflow = EnterpriseWorkflow()
workflow_monitoring = WorkflowMonitoring()
