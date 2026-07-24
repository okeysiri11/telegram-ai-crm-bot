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



from applications.enterprise_hub.simulation_engine.models import SIM_STATUSES


class SimulationScheduler:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def schedule(
        self,
        *,
        scenario_id: str,
        run_at: str = "immediate",
        priority: int = 5,
    ) -> dict[str, Any]:
        if not scenario_id:
            raise ValidationError("scenario_id is required")
        if not self.store.esi_scenarios.get(scenario_id):
            raise NotFoundError(f"scenario not found: {scenario_id}")
        sid = _id("esi_sched")
        return self.store.esi_schedules.save(
            sid,
            {
                "schedule_id": sid,
                "scenario_id": scenario_id,
                "run_at": run_at,
                "priority": int(priority),
                "status": "scheduled",
                "created_at": _now(),
            },
        )

    def execute(self, *, schedule_id: str) -> dict[str, Any]:
        item = self.store.esi_schedules.get(schedule_id)
        if not item:
            raise NotFoundError(f"schedule not found: {schedule_id}")
        item["status"] = "running"
        self.store.esi_schedules.save(schedule_id, item)
        from applications.enterprise_hub.simulation_engine.scenario_engine import ScenarioEngine
        run = ScenarioEngine(self.store).run(scenario_id=item["scenario_id"])
        item["status"] = "completed"
        item["run_id"] = run["run_id"]
        item["completed_at"] = _now()
        self.store.esi_schedules.save(schedule_id, item)
        return item

    def status(self) -> dict[str, Any]:
        items = self.store.esi_schedules.list_all()
        by = {}
        for i in items:
            s = i.get("status", "?")
            by[s] = by.get(s, 0) + 1
        return {"schedules": len(items), "by_status": by}
