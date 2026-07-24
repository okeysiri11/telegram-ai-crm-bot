"""Simulation Scheduler — manual, cron, Event Bus, and continuous runs."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store
from applications.enterprise_hub.simulation_engine.models import SCHEDULE_MODES


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class SimulationScheduler:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def schedule(
        self,
        *,
        scenario_id: str,
        mode: str = "manual",
        run_at: str = "immediate",
        priority: int = 5,
        event_type: str | None = None,
        interval_sec: int | None = None,
    ) -> dict[str, Any]:
        if not scenario_id:
            raise ValidationError("scenario_id is required")
        if mode not in SCHEDULE_MODES:
            raise ValidationError(f"invalid schedule mode: {mode}")
        if not self.store.esi_scenarios.get(scenario_id):
            raise NotFoundError(f"scenario not found: {scenario_id}")
        if mode == "event_bus" and not event_type:
            raise ValidationError("event_type required for event_bus mode")
        if mode == "continuous" and (interval_sec is None or int(interval_sec) <= 0):
            raise ValidationError("interval_sec must be positive for continuous mode")
        sid = _id("esi_sched")
        status = "continuous" if mode == "continuous" else "scheduled"
        return self.store.esi_schedules.save(
            sid,
            {
                "schedule_id": sid,
                "scenario_id": scenario_id,
                "mode": mode,
                "run_at": run_at,
                "priority": int(priority),
                "event_type": event_type,
                "interval_sec": int(interval_sec) if interval_sec is not None else None,
                "status": status,
                "runs": 0,
                "created_at": _now(),
            },
        )

    def run_manual(self, *, scenario_id: str, priority: int = 1) -> dict[str, Any]:
        sched = self.schedule(scenario_id=scenario_id, mode="manual", run_at="immediate", priority=priority)
        return self.execute(schedule_id=sched["schedule_id"])

    def on_event(self, *, event_type: str, payload: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Trigger all event_bus schedules matching event_type."""
        results = []
        for item in self.store.esi_schedules.list_all():
            if item.get("mode") == "event_bus" and item.get("event_type") == event_type:
                results.append(self.execute(schedule_id=item["schedule_id"], trigger={"event_type": event_type, "payload": payload or {}}))
        return results

    def tick_continuous(self) -> list[dict[str, Any]]:
        """Advance continuous simulations by one iteration each."""
        results = []
        for item in self.store.esi_schedules.list_all():
            if item.get("mode") == "continuous" and item.get("status") in ("continuous", "scheduled", "running"):
                results.append(self.execute(schedule_id=item["schedule_id"], keep_continuous=True))
        return results

    def execute(
        self,
        *,
        schedule_id: str,
        trigger: dict[str, Any] | None = None,
        keep_continuous: bool = False,
    ) -> dict[str, Any]:
        item = self.store.esi_schedules.get(schedule_id)
        if not item:
            raise NotFoundError(f"schedule not found: {schedule_id}")
        item["status"] = "running"
        self.store.esi_schedules.save(schedule_id, item)
        from applications.enterprise_hub.simulation_engine.scenario_engine import ScenarioEngine

        run = ScenarioEngine(self.store).run(scenario_id=item["scenario_id"])
        item["runs"] = int(item.get("runs", 0)) + 1
        item["run_id"] = run["run_id"]
        item["last_trigger"] = trigger
        item["completed_at"] = _now()
        if keep_continuous or item.get("mode") == "continuous":
            item["status"] = "continuous"
        else:
            item["status"] = "completed"
        self.store.esi_schedules.save(schedule_id, item)
        return item

    def status(self) -> dict[str, Any]:
        items = self.store.esi_schedules.list_all()
        by_status: dict[str, int] = {}
        by_mode: dict[str, int] = {}
        for i in items:
            s = i.get("status", "?")
            m = i.get("mode", "manual")
            by_status[s] = by_status.get(s, 0) + 1
            by_mode[m] = by_mode.get(m, 0) + 1
        return {"schedules": len(items), "by_status": by_status, "by_mode": by_mode}
