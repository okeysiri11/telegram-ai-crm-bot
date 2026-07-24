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



class ProcessKpi:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def report(self, *, process_id: str) -> dict[str, Any]:
        process = self.store.epm_processes.get(process_id)
        if not process:
            raise NotFoundError(f"process not found: {process_id}")
        perfs = [p for p in self.store.epm_performance.list_all() if p.get("process_id") == process_id]
        confs = [c for c in self.store.epm_conformance.list_all() if c.get("process_id") == process_id]
        avg_dur = perfs[-1]["avg_duration_hours"] if perfs else 3.5 * len(process.get("steps") or [])
        cost = perfs[-1]["cost"] if perfs else 25 * len(process.get("steps") or [])
        sla_ok = 1.0
        if confs:
            viol = confs[-1].get("violation_count", 0)
            sla_ok = max(0.0, 1.0 - 0.1 * viol)
        kid = _id("epm_kpi")
        return self.store.epm_analytics.save(
            kid,
            {
                "analytics_id": kid,
                "kind": "kpi",
                "process_id": process_id,
                "sla_compliance": round(sla_ok, 3),
                "avg_duration_hours": avg_dur,
                "process_cost": cost,
                "throughput": sum(int(v.get("count", 1)) for v in process.get("variants") or []),
                "automation_pct": 35.0,
                "error_rate": round(1 - sla_ok, 3),
                "success_completion_pct": round(100 * sla_ok, 2),
                "at": _now(),
            },
        )
