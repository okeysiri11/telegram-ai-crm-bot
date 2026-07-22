# Dispatch Engine — terminal move jobs and equipment assignment.

from __future__ import annotations

import time

from applications.port_erp.equipment.engine import EquipmentManager, equipment_manager
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.store import PortStore, port_store
from applications.port_erp.terminal_operations.models import (
    DispatchJob,
    DispatchStatus,
    EquipmentStatus,
)


class DispatchEngine:
    def __init__(
        self,
        store: PortStore | None = None,
        equipment: EquipmentManager | None = None,
    ) -> None:
        self._store = store or port_store
        self._equipment = equipment or equipment_manager

    def create_job(self, job: DispatchJob) -> DispatchJob:
        if not job.terminal_id:
            raise ValidationError("terminal_id is required")
        return self._store.dispatch_jobs.save(job.job_id, job)

    def get_job(self, job_id: str) -> DispatchJob:
        job = self._store.dispatch_jobs.get(job_id)
        if job is None:
            raise NotFoundError("DispatchJob", job_id)
        return job

    def list_jobs(self, *, terminal_id: str | None = None, status: DispatchStatus | None = None) -> list[DispatchJob]:
        items = self._store.dispatch_jobs.list_all()
        if terminal_id:
            items = [j for j in items if j.terminal_id == terminal_id]
        if status:
            items = [j for j in items if j.status == status]
        return items

    def assign_equipment(self, job_id: str, *, equipment_id: str = "") -> DispatchJob:
        job = self.get_job(job_id)
        if equipment_id:
            eq = self._equipment.get(equipment_id)
        else:
            available = self._equipment.available(terminal_id=job.terminal_id)
            if not available:
                raise ValidationError("no available equipment")
            eq = available[0]
        self._equipment.set_status(eq.equipment_id, EquipmentStatus.ASSIGNED)
        job.equipment_id = eq.equipment_id
        job.status = DispatchStatus.ASSIGNED
        return self._store.dispatch_jobs.save(job_id, job)

    def start(self, job_id: str) -> DispatchJob:
        job = self.get_job(job_id)
        if job.status not in (DispatchStatus.ASSIGNED, DispatchStatus.PENDING):
            raise ValidationError("job cannot be started")
        if job.equipment_id:
            self._equipment.set_status(job.equipment_id, EquipmentStatus.WORKING)
        job.status = DispatchStatus.IN_PROGRESS
        return self._store.dispatch_jobs.save(job_id, job)

    def complete(self, job_id: str) -> DispatchJob:
        job = self.get_job(job_id)
        job.status = DispatchStatus.COMPLETED
        job.completed_at = time.time()
        if job.equipment_id:
            self._equipment.set_status(job.equipment_id, EquipmentStatus.AVAILABLE)
        return self._store.dispatch_jobs.save(job_id, job)


dispatch_engine = DispatchEngine()
