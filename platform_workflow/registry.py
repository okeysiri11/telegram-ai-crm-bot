"""Workflow Registry — versioned draft / published / archived definitions."""

from __future__ import annotations

import time
from typing import Any

from platform_workflow.runtime_models import (
    RegistryStatus,
    WorkflowDefinition,
    WorkflowVersionRecord,
)


class WorkflowRegistry:
    def __init__(self) -> None:
        self._defs: dict[str, WorkflowDefinition] = {}
        self._versions: dict[str, list[WorkflowVersionRecord]] = {}

    def reset(self) -> None:
        self._defs.clear()
        self._versions.clear()

    def register(self, definition: WorkflowDefinition | dict[str, Any]) -> WorkflowDefinition:
        wf = definition if isinstance(definition, WorkflowDefinition) else WorkflowDefinition.from_dict(definition)
        if wf.workflow_id in self._defs:
            raise ValueError(f"workflow already registered: {wf.workflow_id}")
        wf.status = RegistryStatus.DRAFT
        self._defs[wf.workflow_id] = wf
        self._record_version(wf, changelog="initial registration")
        return wf

    def update(self, workflow_id: str, patch: dict[str, Any]) -> WorkflowDefinition:
        wf = self.get(workflow_id)
        if wf.status == RegistryStatus.ARCHIVED:
            raise ValueError("cannot update archived workflow")
        data = wf.to_dict()
        data.update({k: v for k, v in patch.items() if k != "workflow_id"})
        if "steps" in patch:
            data["steps"] = patch["steps"]
        new_wf = WorkflowDefinition.from_dict(data)
        new_wf.updated_at = time.time()
        version_bumped = new_wf.version != wf.version
        self._defs[workflow_id] = new_wf
        if version_bumped:
            self._record_version(new_wf, changelog=str(patch.get("changelog") or "version update"))
        return new_wf

    def get(self, workflow_id: str) -> WorkflowDefinition:
        wf = self._defs.get(workflow_id)
        if wf is None:
            raise KeyError(f"workflow not found: {workflow_id}")
        return wf

    def list_workflows(
        self,
        *,
        status: str | None = None,
        published_only: bool = False,
    ) -> list[WorkflowDefinition]:
        rows = list(self._defs.values())
        if status:
            rows = [w for w in rows if (w.status.value if isinstance(w.status, RegistryStatus) else w.status) == status]
        if published_only:
            rows = [w for w in rows if w.status == RegistryStatus.PUBLISHED]
        return sorted(rows, key=lambda w: w.name.lower())

    def publish(self, workflow_id: str) -> WorkflowDefinition:
        wf = self.get(workflow_id)
        if wf.status == RegistryStatus.ARCHIVED:
            raise ValueError("cannot publish archived workflow")
        wf.status = RegistryStatus.PUBLISHED
        wf.published_at = time.time()
        wf.updated_at = time.time()
        self._record_version(wf, changelog="published")
        return wf

    def archive(self, workflow_id: str) -> WorkflowDefinition:
        wf = self.get(workflow_id)
        wf.status = RegistryStatus.ARCHIVED
        wf.updated_at = time.time()
        return wf

    def versions(self, workflow_id: str) -> list[WorkflowVersionRecord]:
        return list(self._versions.get(workflow_id, []))

    def activate_version(self, workflow_id: str, version: str) -> WorkflowDefinition:
        versions = self._versions.get(workflow_id) or []
        target = next((v for v in versions if v.version == version), None)
        if target is None:
            raise KeyError(f"version not found: {workflow_id}@{version}")
        for v in versions:
            v.is_active = v.version == version
        wf = WorkflowDefinition.from_dict(target.snapshot)
        wf.status = self._defs[workflow_id].status
        self._defs[workflow_id] = wf
        return wf

    def _record_version(self, wf: WorkflowDefinition, *, changelog: str) -> WorkflowVersionRecord:
        for existing in self._versions.get(wf.workflow_id, []):
            existing.is_active = False
        rec = WorkflowVersionRecord(
            workflow_id=wf.workflow_id,
            version=wf.version,
            snapshot=wf.to_dict(),
            changelog=changelog,
            is_active=True,
        )
        self._versions.setdefault(wf.workflow_id, []).append(rec)
        return rec


workflow_registry = WorkflowRegistry()
