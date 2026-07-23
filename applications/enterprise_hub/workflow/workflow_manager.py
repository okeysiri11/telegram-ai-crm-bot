"""Workflow manager — definitions, builder blocks, versioning."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store
from applications.enterprise_hub.workflow.models import BLOCK_TYPES, TRIGGERS


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class WorkflowManager:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def create(
        self,
        *,
        name: str,
        trigger: str,
        blocks: list[dict[str, Any]] | None = None,
        module: str = "enterprise",
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("name required")
        tr = trigger.lower().strip()
        if tr not in TRIGGERS:
            raise ValidationError(f"trigger must be one of {list(TRIGGERS)}")
        steps = blocks or [{"type": "start"}, {"type": "finish"}]
        for block in steps:
            bt = str(block.get("type", "")).lower()
            if bt not in BLOCK_TYPES:
                raise ValidationError(f"block type must be one of {list(BLOCK_TYPES)}")
        wid = _id("wf_def")
        return self.store.wf_definitions.save(
            wid,
            {
                "workflow_id": wid,
                "name": name,
                "trigger": tr,
                "module": module,
                "blocks": steps,
                "version": 1,
                "status": "draft",
                "at": _now(),
            },
        )

    def add_block(self, *, workflow_id: str, block_type: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
        wf = self.store.wf_definitions.get(workflow_id)
        if wf is None:
            raise NotFoundError(f"workflow not found: {workflow_id}")
        bt = block_type.lower().strip()
        if bt not in BLOCK_TYPES:
            raise ValidationError(f"block type must be one of {list(BLOCK_TYPES)}")
        blocks = list(wf.get("blocks") or [])
        # insert before finish if present
        finish_idx = next((i for i, b in enumerate(blocks) if b.get("type") == "finish"), len(blocks))
        blocks.insert(finish_idx, {"type": bt, "config": config or {}})
        wf["blocks"] = blocks
        wf["at"] = _now()
        return self.store.wf_definitions.save(workflow_id, wf)

    def publish(self, *, workflow_id: str) -> dict[str, Any]:
        wf = self.store.wf_definitions.get(workflow_id)
        if wf is None:
            raise NotFoundError(f"workflow not found: {workflow_id}")
        wf["status"] = "published"
        wf["at"] = _now()
        return self.store.wf_definitions.save(workflow_id, wf)

    def version(self, *, workflow_id: str, note: str = "") -> dict[str, Any]:
        wf = self.store.wf_definitions.get(workflow_id)
        if wf is None:
            raise NotFoundError(f"workflow not found: {workflow_id}")
        wf["version"] = int(wf.get("version", 1)) + 1
        wf["at"] = _now()
        self.store.wf_definitions.save(workflow_id, wf)
        vid = _id("wf_ver")
        return self.store.wf_versions.save(
            vid,
            {
                "version_id": vid,
                "workflow_id": workflow_id,
                "version": wf["version"],
                "note": note,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "definitions": self.store.wf_definitions.count(),
            "versions": self.store.wf_versions.count(),
            "triggers": list(TRIGGERS),
            "blocks": list(BLOCK_TYPES),
        }
