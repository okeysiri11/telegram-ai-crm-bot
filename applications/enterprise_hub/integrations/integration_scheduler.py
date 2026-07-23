"""Integration scheduler — scheduled sync jobs."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class IntegrationScheduler:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def schedule(
        self,
        *,
        integration_id: str,
        expression: str = "0 * * * *",
        sync_mode: str = "incremental",
    ) -> dict[str, Any]:
        if self.store.eip_registry.get(integration_id) is None:
            raise NotFoundError(f"integration not found: {integration_id}")
        if not expression:
            raise ValidationError("expression required")
        sid = _id("eip_sched")
        return self.store.eip_schedules.save(
            sid,
            {
                "schedule_id": sid,
                "integration_id": integration_id,
                "expression": expression,
                "sync_mode": sync_mode,
                "status": "scheduled",
                "at": _now(),
            },
        )

    def fire(self, *, schedule_id: str) -> dict[str, Any]:
        sched = self.store.eip_schedules.get(schedule_id)
        if sched is None:
            raise NotFoundError(f"schedule not found: {schedule_id}")
        sched["status"] = "fired"
        sched["at"] = _now()
        self.store.eip_schedules.save(schedule_id, sched)
        fid = _id("eip_fire")
        return self.store.eip_schedule_fires.save(
            fid,
            {
                "fire_id": fid,
                "schedule_id": schedule_id,
                "integration_id": sched["integration_id"],
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "schedules": self.store.eip_schedules.count(),
            "fires": self.store.eip_schedule_fires.count(),
        }
