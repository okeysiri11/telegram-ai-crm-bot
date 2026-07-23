"""Workflow validator — structural and runtime checks."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store
from applications.enterprise_hub.workflow.models import BLOCK_TYPES


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class WorkflowValidator:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def validate(self, *, workflow_id: str) -> dict[str, Any]:
        wf = self.store.wf_definitions.get(workflow_id)
        if wf is None:
            raise NotFoundError(f"workflow not found: {workflow_id}")
        blocks = wf.get("blocks") or []
        errors: list[str] = []
        if not blocks:
            errors.append("blocks empty")
        types = [str(b.get("type", "")).lower() for b in blocks]
        if "start" not in types:
            errors.append("missing start")
        if "finish" not in types:
            errors.append("missing finish")
        for t in types:
            if t not in BLOCK_TYPES:
                errors.append(f"invalid block: {t}")
        if types and types[0] != "start":
            errors.append("start must be first")
        valid = not errors
        vid = _id("wf_val")
        return self.store.wf_validations.save(
            vid,
            {
                "validation_id": vid,
                "workflow_id": workflow_id,
                "valid": valid,
                "errors": errors,
                "at": _now(),
            },
        )

    def require_valid(self, *, workflow_id: str) -> dict[str, Any]:
        result = self.validate(workflow_id=workflow_id)
        if not result["valid"]:
            raise ValidationError(f"workflow invalid: {result['errors']}")
        return result

    def status(self) -> dict[str, Any]:
        return {"validations": self.store.wf_validations.count()}
