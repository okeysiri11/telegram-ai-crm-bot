"""Enterprise Workflow Registry — Sprint 24.1."""

from __future__ import annotations

from typing import Any


class WorkflowRegistry:
    def create(
        self,
        *,
        workflow_id: str,
        name: str,
        description: str = "",
        industry: str = "beauty",
        version: str = "1.0",
        owner: str = "platform_owner",
        status: str = "draft",
    ) -> dict[str, Any]:
        if not workflow_id or not name:
            raise ValueError("workflow_id and name are required")
        return {
            "workflow_id": workflow_id,
            "name": name.strip(),
            "description": description,
            "industry": industry,
            "version": version,
            "status": status,
            "owner": owner,
            "change_history": [{"version": version, "event": "created"}],
            "nodes": [],
            "policy": "requires_owner",
        }

    def bump_version(self, workflow: dict[str, Any], *, note: str = "updated") -> dict[str, Any]:
        updated = dict(workflow)
        parts = str(updated.get("version", "1.0")).split(".")
        major, minor = int(parts[0]), int(parts[1]) if len(parts) > 1 else 0
        new_ver = f"{major}.{minor + 1}"
        hist = list(updated.get("change_history") or [])
        hist.append({"version": new_ver, "event": note})
        updated["version"] = new_ver
        updated["change_history"] = hist
        return updated
