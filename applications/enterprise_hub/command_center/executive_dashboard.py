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

from applications.enterprise_hub.command_center.dashboard_manager import DashboardManager


class ExecutiveDashboard:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.manager = DashboardManager(self.store)

    def render(self, *, health_score: float = 0.82, workspace_id: str | None = None) -> dict[str, Any]:
        dash = self.manager.create(kind="executive", workspace_id=workspace_id)
        eid = _id("ecc_exec")
        record = {
            "executive_id": eid,
            "dashboard_id": dash["dashboard_id"],
            "company_state": "operational",
            "kpi": {
                "revenue_index": 1.12,
                "margin": 0.18,
                "nps": 62,
                "on_time_delivery": 0.91,
            },
            "cashflow": {"inflow": 12.4, "outflow": 9.8, "net": 2.6},
            "projects": [{"name": "Port Expansion", "progress": 0.64}, {"name": "AI Rollout", "progress": 0.71}],
            "department_load": {"ops": 0.78, "finance": 0.55, "logistics": 0.82, "ai": 0.67},
            "ai_status": {"agents_active": 14, "orchestrator": "healthy"},
            "critical_events": 2,
            "forecasts": {"revenue_next_q": 1.08, "risk_index": 0.22},
            "health_score": health_score,
            "rendered_at": _now(),
        }
        self.store.ecc_executive.save(eid, record)
        return record
