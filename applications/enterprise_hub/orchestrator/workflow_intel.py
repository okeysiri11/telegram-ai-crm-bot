"""Workflow intelligence — templates, dynamic gen, parallel/sequential, conditional, approval."""

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


class WorkflowIntelligence:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.template_kinds = list(DEFAULT_CONFIG.orch_template_kinds)

    def create_template(
        self, *, name: str, kind: str = "sequential", steps: list[str] | None = None
    ) -> dict[str, Any]:
        k = kind.lower().strip()
        if k not in self.template_kinds:
            raise ValidationError(f"kind must be one of {self.template_kinds}")
        if not name:
            raise ValidationError("name required")
        tid = _id("orch_tpl")
        return self.store.orch_templates.save(
            tid,
            {
                "template_id": tid,
                "name": name,
                "kind": k,
                "steps": steps or [],
                "at": _now(),
            },
        )

    def generate(
        self, *, name: str, intent: str, platforms: list[str] | None = None
    ) -> dict[str, Any]:
        if not name or not intent:
            raise ValidationError("name and intent required")
        gid = _id("orch_dyn")
        plats = platforms or ["finance"]
        steps = [f"route:{p}" for p in plats] + ["validate", "complete"]
        return self.store.orch_dynamic.save(
            gid,
            {
                "dynamic_id": gid,
                "name": name,
                "intent": intent,
                "platforms": plats,
                "steps": steps,
                "at": _now(),
            },
        )

    def add_approval(self, *, workflow_ref: str, approver: str = "executive") -> dict[str, Any]:
        if not workflow_ref:
            raise ValidationError("workflow_ref required")
        aid = _id("orch_apr")
        return self.store.orch_approvals.save(
            aid,
            {
                "approval_id": aid,
                "workflow_ref": workflow_ref,
                "approver": approver,
                "status": "pending",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "templates": self.store.orch_templates.count(),
            "dynamic": self.store.orch_dynamic.count(),
            "approvals": self.store.orch_approvals.count(),
            "kinds": self.template_kinds,
        }
