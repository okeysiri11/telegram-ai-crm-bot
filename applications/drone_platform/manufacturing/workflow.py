"""Production workflow stages (Sprint 11.6)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.exceptions import NotFoundError, ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store


WORKFLOW_STAGES = (
    "receive_components",
    "incoming_inspection",
    "storage",
    "picking",
    "assembly",
    "programming",
    "calibration",
    "quality_control",
    "flight_testing",
    "packaging",
    "shipping",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ProductionWorkflow:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def start_job(self, *, order_id: str, assembly_id: str = "", serial_number: str = "") -> dict[str, Any]:
        jid = f"wf_{uuid.uuid4().hex[:12]}"
        job = {
            "job_id": jid,
            "order_id": order_id,
            "assembly_id": assembly_id,
            "serial_number": serial_number,
            "stages": [{ "name": s, "status": "pending"} for s in WORKFLOW_STAGES],
            "current_stage": WORKFLOW_STAGES[0],
            "status": "active",
            "history": [{"event": "started", "at": _now()}],
            "created_at": _now(),
        }
        self.store.workflow_jobs.save(jid, job)
        return job

    def get(self, job_id: str) -> dict[str, Any]:
        item = self.store.workflow_jobs.get(job_id)
        if item is None:
            raise NotFoundError("workflow_job", job_id)
        return item

    def advance(self, job_id: str, *, notes: str = "", result: str = "pass") -> dict[str, Any]:
        job = self.get(job_id)
        current = job["current_stage"]
        for stage in job["stages"]:
            if stage["name"] == current and stage["status"] == "pending":
                stage["status"] = "done" if result == "pass" else "failed"
                stage["notes"] = notes
                stage["completed_at"] = _now()
                break
        else:
            raise ValidationError(f"Stage not pending: {current}")
        if result != "pass":
            job["status"] = "blocked"
            job["history"].append({"event": "failed", "stage": current, "at": _now()})
            self.store.workflow_jobs.save(job_id, job)
            return job
        # move next
        names = [s["name"] for s in job["stages"]]
        idx = names.index(current)
        if idx + 1 < len(names):
            job["current_stage"] = names[idx + 1]
        else:
            job["current_stage"] = "complete"
            job["status"] = "complete"
        job["history"].append({"event": "advanced", "from": current, "to": job["current_stage"], "at": _now()})
        self.store.workflow_jobs.save(job_id, job)
        return job

    def list(self) -> list[dict[str, Any]]:
        return self.store.workflow_jobs.list_all()

    def status(self) -> dict[str, Any]:
        return {
            "production_workflow": "1.0",
            "stages": list(WORKFLOW_STAGES),
            "jobs": self.store.workflow_jobs.count(),
        }


production_workflow = ProductionWorkflow()
