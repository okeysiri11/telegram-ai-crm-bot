"""Workflow action runners."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store
from applications.enterprise_hub.workflow.models import ACTION_TYPES


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def run_action(
    store: EnterpriseHubStore,
    *,
    action_type: str,
    target: str = "",
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    at = action_type.lower().strip()
    if at not in ACTION_TYPES:
        raise ValidationError(f"action_type must be one of {list(ACTION_TYPES)}")
    aid = _id("wf_act")
    return store.wf_actions.save(
        aid,
        {
            "action_id": aid,
            "action_type": at,
            "target": target,
            "payload": payload or {},
            "status": "completed",
            "at": _now(),
        },
    )


class ActionRegistry:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def execute(
        self,
        *,
        action_type: str,
        target: str = "",
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return run_action(self.store, action_type=action_type, target=target, payload=payload)

    def status(self) -> dict[str, Any]:
        return {"actions": self.store.wf_actions.count(), "types": list(ACTION_TYPES)}
