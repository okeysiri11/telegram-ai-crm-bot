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




class PerformanceMining:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def analyze(self, *, process_id: str) -> dict[str, Any]:
        process = self.store.epm_processes.get(process_id)
        if not process:
            raise NotFoundError(f"process not found: {process_id}")
        steps = process.get("steps") or []
        variants = process.get("variants") or []
        case_count = sum(int(v.get("count", 1)) for v in variants) or 1
        avg_duration = 3.5 * len(steps)
        wait = 1.2 * len(steps)
        cost = 25 * len(steps)
        rework = sum(1 for v in variants if len(v.get("path") or []) != len(set(v.get("path") or [])))
        pid = _id("epm_perf")
        return self.store.epm_performance.save(
            pid,
            {
                "performance_id": pid,
                "process_id": process_id,
                "avg_duration_hours": round(avg_duration, 2),
                "wait_hours": round(wait, 2),
                "cost": cost,
                "rework_count": rework,
                "efficiency": round(max(0.1, 1 - rework / case_count), 3),
                "participant_load": min(1.0, round(case_count / 50, 3)),
                "at": _now(),
            },
        )
