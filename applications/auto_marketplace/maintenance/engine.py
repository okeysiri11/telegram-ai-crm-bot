# Maintenance Engine — schedules, mileage/time tracking, fleet plans.

from __future__ import annotations

import time

from applications.auto_marketplace.service_centers.models import MaintenancePlan, MaintenanceSchedule
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class VehicleMaintenanceEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def create_plan(self, plan: MaintenancePlan) -> MaintenancePlan:
        if not plan.vehicle_id and not plan.fleet_id:
            raise ValidationError("vehicle_id or fleet_id is required")
        if not plan.tasks:
            plan.tasks = ["oil_change", "filters", "inspection"]
        return self._store.maintenance_plans.save(plan.plan_id, plan)

    def schedule(
        self,
        *,
        plan_id: str,
        current_mileage_km: int = 0,
        now: float | None = None,
    ) -> MaintenanceSchedule:
        plan = self._store.maintenance_plans.get(plan_id)
        if plan is None:
            raise NotFoundError("MaintenancePlan", plan_id)
        now = now if now is not None else time.time()
        item = MaintenanceSchedule(
            plan_id=plan_id,
            vehicle_id=plan.vehicle_id,
            due_mileage_km=current_mileage_km + plan.interval_km,
            due_at=now + plan.interval_days * 86400,
        )
        return self._store.maintenance_schedules.save(item.schedule_id, item)

    def track_mileage(self, vehicle_id: str, mileage_km: int) -> list[dict]:
        due = []
        for sched in self._store.maintenance_schedules.list_all():
            if sched.vehicle_id == vehicle_id and sched.status == "scheduled":
                if mileage_km >= sched.due_mileage_km:
                    sched.status = "due"
                    self._store.maintenance_schedules.save(sched.schedule_id, sched)
                    due.append(sched.to_dict())
        return due

    def reminders(self, *, vehicle_id: str = "", now: float | None = None) -> list[dict]:
        now = now if now is not None else time.time()
        items = []
        for sched in self._store.maintenance_schedules.list_all():
            if vehicle_id and sched.vehicle_id != vehicle_id:
                continue
            upcoming = sched.status == "scheduled" and sched.due_at <= now + 7 * 86400
            overdue = sched.status == "due"
            if upcoming or overdue:
                reminder = {
                    "schedule_id": sched.schedule_id,
                    "vehicle_id": sched.vehicle_id,
                    "due_at": sched.due_at,
                    "due_mileage_km": sched.due_mileage_km,
                    "message": "Maintenance due" if overdue else "Maintenance due soon",
                }
                self._store.maintenance_reminders.save(sched.schedule_id, reminder)
                items.append(reminder)
        return items

    def fleet_plans(self, fleet_id: str) -> list[MaintenancePlan]:
        return [p for p in self._store.maintenance_plans.list_all() if p.fleet_id == fleet_id]

    def list_schedules(self, *, vehicle_id: str = "") -> list[MaintenanceSchedule]:
        items = self._store.maintenance_schedules.list_all()
        if vehicle_id:
            items = [s for s in items if s.vehicle_id == vehicle_id]
        return items

    def metrics(self) -> dict:
        return {
            "plans": self._store.maintenance_plans.count(),
            "schedules": self._store.maintenance_schedules.count(),
            "reminders": self._store.maintenance_reminders.count(),
        }


vehicle_maintenance_engine = VehicleMaintenanceEngine()
