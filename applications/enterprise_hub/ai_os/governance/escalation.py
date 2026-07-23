"""Escalation rules."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class EscalationEngine:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def escalate(self, *, task_id: str, reason: str, level: str = "ops") -> dict[str, Any]:
        eid = _id("aios_esc")
        return self.store.aios_escalations.save(
            eid,
            {
                "escalation_id": eid,
                "task_id": task_id,
                "reason": reason,
                "level": level,
                "status": "open",
                "at": _now(),
            },
        )
