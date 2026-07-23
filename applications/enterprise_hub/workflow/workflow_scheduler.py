"""Workflow scheduler — cron, interval, once, delayed, calendar."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store
from applications.enterprise_hub.workflow.models import SCHEDULE_KINDS


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class WorkflowScheduler:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def schedule(
        self,
        *,
        workflow_id: str,
        kind: str,
        expression: str = "",
        delay_seconds: int = 0,
    ) -> dict[str, Any]:
        if self.store.wf_definitions.get(workflow_id) is None:
            raise NotFoundError(f"workflow not found: {workflow_id}")
        k = kind.lower().strip()
        if k not in SCHEDULE_KINDS:
            raise ValidationError(f"kind must be one of {list(SCHEDULE_KINDS)}")
        sid = _id("wf_sched")
        return self.store.wf_schedules.save(
            sid,
            {
                "schedule_id": sid,
                "workflow_id": workflow_id,
                "kind": k,
                "expression": expression,
                "delay_seconds": int(delay_seconds),
                "status": "scheduled",
                "at": _now(),
            },
        )

    def fire(self, *, schedule_id: str) -> dict[str, Any]:
        sched = self.store.wf_schedules.get(schedule_id)
        if sched is None:
            raise NotFoundError(f"schedule not found: {schedule_id}")
        sched["status"] = "fired"
        sched["at"] = _now()
        self.store.wf_schedules.save(schedule_id, sched)
        fid = _id("wf_fire")
        return self.store.wf_schedule_fires.save(
            fid,
            {
                "fire_id": fid,
                "schedule_id": schedule_id,
                "workflow_id": sched["workflow_id"],
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "schedules": self.store.wf_schedules.count(),
            "fires": self.store.wf_schedule_fires.count(),
            "kinds": list(SCHEDULE_KINDS),
        }
