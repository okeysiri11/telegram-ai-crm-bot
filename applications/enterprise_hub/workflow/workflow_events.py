"""Workflow domain events."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class WorkflowEvents:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def emit(
        self,
        *,
        event_type: str,
        workflow_id: str = "",
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not event_type:
            raise ValidationError("event_type required")
        eid = _id("wf_evt")
        return self.store.wf_events.save(
            eid,
            {
                "event_id": eid,
                "event_type": event_type,
                "workflow_id": workflow_id,
                "payload": payload or {},
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"events": self.store.wf_events.count()}
