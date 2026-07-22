# Fleet Dispatch — vehicle/driver/task/route/emergency + AI optimization.

from __future__ import annotations

import time

from applications.auto_marketplace.fleet.models import FleetDispatchJob
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class FleetDispatchEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def create_job(self, job: FleetDispatchJob) -> FleetDispatchJob:
        if not job.task:
            raise ValidationError("task is required")
        if not job.scheduled_at:
            job.scheduled_at = time.time() + 1800
        job.status = "queued"
        return self._store.fleet_dispatch_jobs.save(job.job_id, job)

    def assign(self, job_id: str, *, fleet_vehicle_id: str, driver_id: str) -> FleetDispatchJob:
        job = self._get(job_id)
        job.fleet_vehicle_id = fleet_vehicle_id
        job.driver_id = driver_id
        job.status = "assigned"
        return self._store.fleet_dispatch_jobs.save(job_id, job)

    def schedule_route(self, job_id: str, route: list[str]) -> FleetDispatchJob:
        job = self._get(job_id)
        job.route = list(route)
        job.status = "scheduled"
        return self._store.fleet_dispatch_jobs.save(job_id, job)

    def emergency(self, *, task: str, fleet_vehicle_id: str = "", driver_id: str = "") -> FleetDispatchJob:
        job = FleetDispatchJob(
            task=task,
            fleet_vehicle_id=fleet_vehicle_id,
            driver_id=driver_id,
            priority=100,
            emergency=True,
            status="dispatched",
            scheduled_at=time.time(),
        )
        return self._store.fleet_dispatch_jobs.save(job.job_id, job)

    def optimize_queue(self) -> list[FleetDispatchJob]:
        jobs = self._store.fleet_dispatch_jobs.list_all()
        ordered = sorted(jobs, key=lambda j: (-int(j.emergency), -j.priority, j.scheduled_at))
        for i, job in enumerate(ordered):
            if job.status == "queued":
                job.status = "optimized"
                job.scheduled_at = time.time() + i * 900
                self._store.fleet_dispatch_jobs.save(job.job_id, job)
        return ordered

    def _get(self, job_id: str) -> FleetDispatchJob:
        item = self._store.fleet_dispatch_jobs.get(job_id)
        if item is None:
            raise NotFoundError("FleetDispatchJob", job_id)
        return item

    def list_jobs(self, *, status: str = "") -> list[FleetDispatchJob]:
        items = self._store.fleet_dispatch_jobs.list_all()
        if status:
            items = [j for j in items if j.status == status]
        return items

    def metrics(self) -> dict:
        items = self._store.fleet_dispatch_jobs.list_all()
        return {
            "jobs": len(items),
            "emergency": len([j for j in items if j.emergency]),
            "queued": len([j for j in items if j.status == "queued"]),
        }


fleet_dispatch_engine = FleetDispatchEngine()
